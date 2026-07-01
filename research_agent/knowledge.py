"""
知识库 —— 基于 Chroma 的 RAG 检索系统

Agent 可以加载本地文档到知识库，然后通过语义搜索查找相关内容。
支持 .md / .txt 格式，从本地文件路径读取。
"""

import os
from typing import Optional

# HuggingFace 镜像（国内网络加速）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


# ============================================================
# 知识库（单例）
# ============================================================

class KnowledgeBase:
    """基于 Chroma 的本地文档知识库"""

    _instance: Optional["KnowledgeBase"] = None

    def __new__(cls, persist_dir: str = ""):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, persist_dir: str = ""):
        if self._initialized:
            return
        self._initialized = True

        import chromadb
        from chromadb.config import Settings

        self._persist_dir = persist_dir or os.path.join(
            os.path.dirname(__file__), "..", "chroma_db"
        )
        os.makedirs(self._persist_dir, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=self._persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )

        self._collection = self._client.get_or_create_collection(
            name="research_knowledge",
            metadata={"hnsw:space": "cosine"},
        )

        self._embedder = None
        self._doc_count = self._collection.count()

    def _get_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(
                "all-MiniLM-L6-v2", device="cpu",
            )
        return self._embedder

    # ============================================================
    # 分块
    # ============================================================

    def _chunk(self, text: str, chunk_size: int = 500, overlap: int = 50):
        """将文本按大小切块，尽量在换行处断开"""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                nl = text.rfind("\n", start, end)
                if nl > start + chunk_size // 2:
                    end = nl
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap
        return chunks

    # ============================================================
    # 从本地文件加载
    # ============================================================

    def load_file(self, filepath: str) -> str:
        """加载本地文件到知识库，支持 .md / .txt"""
        filepath = os.path.abspath(filepath)
        if not os.path.exists(filepath):
            return f"错误：文件不存在 - {filepath}"

        _, ext = os.path.splitext(filepath)
        if ext.lower() not in (".md", ".txt"):
            return f"错误：不支持的文件格式 {ext}，仅支持 .md / .txt"

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return self.add_document(os.path.basename(filepath), content)

    def load_directory(self, dirpath: str, pattern: str = "*.md") -> str:
        """批量加载目录下的所有文档"""
        import glob
        dirpath = os.path.abspath(dirpath)
        if not os.path.isdir(dirpath):
            return f"错误：目录不存在 - {dirpath}"

        files = glob.glob(os.path.join(dirpath, pattern))
        if not files:
            return f"目录下没有匹配 {pattern} 的文件"

        results = []
        for fpath in files:
            result = self.load_file(fpath)
            results.append(result)

        success = sum(1 for r in results if "错误" not in r)
        return f"加载完成：{success}/{len(files)} 个文件成功\n" + "\n".join(results)

    # ============================================================
    # 核心：添加文档 & 检索
    # ============================================================

    def add_document(self, filename: str, content: str) -> str:
        """添加文档内容到知识库"""
        if not content.strip():
            return f"错误：{filename} 内容为空"

        embedder = self._get_embedder()
        chunks = self._chunk(content)

        if not chunks:
            return f"错误：{filename} 无法分块"

        embeddings = embedder.encode(chunks, show_progress_bar=False).tolist()
        ids = [f"doc_{self._doc_count + i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "chunk": i} for i in range(len(chunks))]

        self._collection.add(
            ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas,
        )
        self._doc_count += len(chunks)

        return f"已加载：{filename}（{len(chunks)} 个片段，共 {len(content)} 字）"

    def query(self, question: str, top_k: int = 3) -> str:
        """语义检索知识库"""
        if self._collection.count() == 0:
            return "知识库为空，请先用 load_document 加载文档。"

        embedder = self._get_embedder()
        q_emb = embedder.encode([question], show_progress_bar=False).tolist()

        results = self._collection.query(
            query_embeddings=q_emb,
            n_results=min(top_k, self._collection.count()),
        )

        if not results["documents"] or not results["documents"][0]:
            return "未找到相关内容。"

        output = ["知识库检索结果："]
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            source = meta.get("source", "未知")
            score = round(1 - dist, 3)
            output.append(f"\n[{i+1}] 来源：{source}（相似度：{score}）")
            output.append(f"    {doc[:200]}...")

        return "\n".join(output)

    def count(self) -> int:
        return self._collection.count()

    def clear(self):
        self._client.delete_collection("research_knowledge")
        self._collection = self._client.get_or_create_collection(
            name="research_knowledge",
        )
        self._doc_count = 0


# ============================================================
# 全局实例
# ============================================================

_kb: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb
