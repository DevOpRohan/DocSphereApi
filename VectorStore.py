import mimetypes
import pickle
import shutil
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

    def store(self, userId, file_path, docId):
        # Add the UUID to URL map entry
        self.uuid_url_map[docId] = file_path

        # Extract MIME type
        mime_type, _ = mimetypes.guess_type(file_path)

        # Only accept pdf, png, jpeg, tiff, docx, pptx, xlsx
        if mime_type not in ['application/pdf', 'image/png', 'image/jpeg', 'image/tiff', 'text/plain'
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                             'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            raise Exception("File type not supported")

        # Step ii: Use OCR to extract contents for each page
        processor = DocumentAIProcessor(project_id, location, processor_id, mime_type)
        page_contents = processor.process_document(file_path)

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

    def euclidean(self, a, b):
        diff = np.array(a) - np.array(b)
        squared_diff = np.square(diff)
        sum_squared_diff = np.sum(squared_diff)
        euclidean_dist = np.sqrt(sum_squared_diff)
        return euclidean_dist

    def hybrid_similarity_comparator(self, a, b, query_embedding):
        if a[0] != b[0]:
            return b[0] - a[0]  # Compare cosine similarity (descending order)
        else:
            # Calculate Euclidean distance and compare (ascending order)
            euclidean_a = self.euclidean(query_embedding, a[4])
            euclidean_b = self.euclidean(query_embedding, b[4])
            return euclidean_a - euclidean_b

    def hybrid_similarity_search(self, userId, query, k):
        # Step i: Generate the embedding of query
        query_embedding = getQueryEmbeddings(query)

        # Step ii: Perform cosine similarity search on all the embeddings of that user
        user_data = self.data.get(userId, [])
        similarities = []

        for docId, contents_with_embeddings in user_data:
            for pageNo, (content, embedding) in enumerate(contents_with_embeddings):
                similarity = self.cosine(query_embedding, embedding)
                similarities.append((similarity, str(docId), pageNo, content, embedding))

        # Step iii: Sort using the hybrid_similarity_comparator function
        sorted_similarities = sorted(similarities, key=lambda x: (-x[0], self.euclidean(query_embedding, x[4])))

        top_k_results = sorted_similarities[:k]

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

    print("Hybrid Search Results")
    result = vectorStore.hybrid_similarity_search(userId, query, k)
    # print result line by line
    for res in result:
        print(res)
"""