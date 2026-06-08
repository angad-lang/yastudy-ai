from dotenv import load_dotenv
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
import uuid
import hashlib

load_dotenv()

docs = []

# 1. Load All PDFs from 'knowledge_base' folder
kb_folder = Path(__file__).parent / "knowledge_base"
if kb_folder.exists():
    for pdf_path in kb_folder.glob("*.pdf"):
        print(f"Loading PDF: {pdf_path.name}...")
        try:
            pdf_loader = PyPDFLoader(file_path=str(pdf_path))
            docs.extend(pdf_loader.load())
        except Exception as e:
            print(f"Failed to load PDF {pdf_path.name}: {e}")
else:
    print(f"No 'knowledge_base' folder found at {kb_folder}")

# 2. Load Website Data
urls_to_scrape = [
   "https://yastudy.com/services/sop",
   "https://yastudy.com/services/lom",
   "https://yastudy.com/services/cv",
   "https://yastudy.com/services/visa",
   "https://yastudy.com/services/passport",
   "https://yastudy.com/services/aps",
   "https://yastudy.com/services/loan",
   "https://yastudy.com/testprep/ielts",
   "https://yastudy.com/testprep/german",
   "https://yastudy.com/mba-india"
]
print("Loading website data...")
for url in urls_to_scrape:
    try:
        web_loader = WebBaseLoader(url)
        docs.extend(web_loader.load())
    except Exception as e:
        print(f"Failed to load URL {url}: {e}")

if not docs:
    print("No documents were loaded. Exiting.")
    exit()

print(f"Total documents loaded: {len(docs)}")

# 3. Split the docs into smaller chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=400
)

chunks = text_splitter.split_documents(documents=docs)
print(f"Split into {len(chunks)} chunks.")

# 4. Generate unique, deterministic IDs for each chunk to prevent duplicates
# Agar chunk ka text same hai, toh UUID same banega aur Qdrant usko overwrite kar dega (duplicate nahi hoga)
chunk_ids = []
for chunk in chunks:
    # Use MD5 hash of the chunk content to create a stable UUID
    chunk_hash = hashlib.md5(chunk.page_content.encode("utf-8")).hexdigest()
    chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_hash))
    chunk_ids.append(chunk_id)

# 5. Vector Embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
)

from app.core.config import settings
from qdrant_client import QdrantClient

# 6. Save to Qdrant (Without force_recreate so it appends)
print("Uploading to Qdrant Vector Database...")

# We create the client explicitly to increase the timeout for large uploads
client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    timeout=60.0
)

vector_store = QdrantVectorStore(
    client=client,
    collection_name=settings.QDRANT_COLLECTION,
    embedding=embedding_model
)

# Upload in batches using add_documents
vector_store.add_documents(documents=chunks, ids=chunk_ids)

print("Indexing of documents done successfully! Data has been appended/updated without duplicates.")