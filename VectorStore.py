import mimetypes
import pickle
import uuid
import numpy as np

from embeddingGenerator import getDocEmbeddings, getQueryEmbeddings
from ocr import DocumentAIProcessor, project_id, location, processor_id, mime_type

import os


class VectorStore:
    def __init__(self, storage_file='vector_store.pkl'):
        self.storage_file = storage_file
        self.data = {}
        self.uuid_map = {}
        self.uuid_url_map = {}  # Added the UUID to URL map

        # Load data from storage file if it exists and is not empty
        if os.path.exists(self.storage_file) and os.path.getsize(self.storage_file) > 0:
            with open(self.storage_file, 'rb') as f:
                self.data, self.uuid_map, self.uuid_url_map = pickle.load(f)
        else:
            with open(self.storage_file, 'wb') as f:
                pickle.dump((self.data, self.uuid_map, self.uuid_url_map), f)

    def save_data(self):
        with open(self.storage_file, 'wb') as f:
            pickle.dump((self.data, self.uuid_map, self.uuid_url_map), f)

    def cosine(self, a, b):
        dot_product = np.dot(a, b)
        magnitude_a = np.linalg.norm(a)
        magnitude_b = np.linalg.norm(b)
        similarity = dot_product / (magnitude_a * magnitude_b)
        return similarity

    def store(self, userId, doc):
        # Step i: Give uuid to doc
        docId = uuid.uuid4()
        # Save the document in the appropriate user directory
        saved_doc_path = f"Docs/{userId}/{docId}"
        os.makedirs(f"Docs/{userId}", exist_ok=True)
        with open(saved_doc_path, "wb") as saved_doc_file:
            saved_doc_file.write(doc.read())

        # Add the UUID to URL map entry
        self.uuid_url_map[docId] = saved_doc_path

        # Extract MIME type
        mime_type, _ = mimetypes.guess_type(doc)

        # Only accept pdf, png, jpeg, tiff, docx, pptx, xlsx
        if mime_type not in ['application/pdf', 'image/png', 'image/jpeg', 'image/tiff',
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                             'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            raise Exception("File type not supported")

        # Step ii: Use OCR to extract contents for each page
        processor = DocumentAIProcessor(project_id, location, processor_id, mime_type)
        page_contents = processor.process_document(doc)

        # Step iii: Generate the embedding of each page/content
        contents_embeddings = getDocEmbeddings(page_contents)
        contents_with_embeddings = list(zip(page_contents, contents_embeddings))

        # Update the user's data
        if userId not in self.data:
            self.data[userId] = []
        self.data[userId].append((docId, contents_with_embeddings))
        self.save_data()
        return docId

    def cosine_similarity_search(self, userId, query, k):
        # Step i: Generate the embedding of query
        query_embedding = getQueryEmbeddings(query)

        # Step ii: Perform cosine similarity search on all the embeddings of that user
        user_data = self.data.get(userId, [])
        similarities = []

        for docId, contents_with_embeddings in user_data:
            for pageNo, (content, embedding) in enumerate(contents_with_embeddings):
                similarity = self.cosine(query_embedding, embedding)
                similarities.append((similarity, str(docId), pageNo, content))

        # Step iii: Return top k content
        top_k_results = sorted(similarities, reverse=True, key=lambda x: x[0])[:k]
        # Replacing the UUID with the document URL
        results = [{'url': self.uuid_url_map[uuid.UUID(res[1])], 'pageNo': res[2] + 1,
                    'content': res[3], 'similarity': res[0]} for res in top_k_results]
        return results


"""
# usage
vectorStore = VectorStore('Persistence/vector_store.pkl')
doc = './Docs/TestDoc.pdf'
userId = 'user1'
# vectorStore.store(userId, doc)
# Let's engage user in console input
while True:
    print("Please enter your query")
    query = input()
    print("Please enter the number of results you want")
    k = int(input())

    result = vectorStore.cosine_similarity_search(userId, query, k)
    # print result line by line
    for res in result:
        print(res)
"""
