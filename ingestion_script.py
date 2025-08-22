import os
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from docx import Document
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Supabase Setup ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --- Embedding Model ---
model = SentenceTransformer('all-MiniLM-L6-v2')
model.max_seq_length = 512

# --- File Paths and Chunking ---
data_dir = "./transcriptions"
CHUNK_SIZE = 500  # Words per chunk

def get_chunks_from_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    full_text = "\n".join(full_text)
    
    # Simple chunking by splitting into a list of words
    words = full_text.split()
    chunks = [' '.join(words[i:i + CHUNK_SIZE]) for i in range(0, len(words), CHUNK_SIZE)]
    return chunks

def process_file(file_path):
    file_name = os.path.basename(file_path)
    print(f"Processing: {file_name}")
    
    chunks = get_chunks_from_docx(file_path)
    
    data_to_insert = []
    for chunk in chunks:
        # Generate embedding for the chunk
        embedding = model.encode(chunk).tolist()
        data_to_insert.append({
            "content": chunk,
            "embedding": embedding,
            "source": file_name
        })

    # Insert data into Supabase
    try:
        supabase.from_("transcription").insert(data_to_insert).execute()
        print(f"✅ Successfully inserted {len(data_to_insert)} chunks from {file_name}")
    except Exception as e:
        print(f"❌ Error inserting data for {file_name}: {e}")

# --- Main Ingestion Loop ---
if __name__ == "__main__":
    if not os.path.exists(data_dir):
        print(f"Error: Directory '{data_dir}' not found. Please create it and place your files inside.")
    else:
        for file in os.listdir(data_dir):
            if file.endswith(".docx"):
                process_file(os.path.join(data_dir, file))