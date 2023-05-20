from typing import Sequence, List
from google.api_core.client_options import ClientOptions
from google.cloud import documentai
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")  # Load environment variables from .env file

project_id = 'vision-386522'
location = 'eu'  # Format is 'us' or 'eu'
processor_id = 'c9677a16c53c916b'  # Create processor before running sample
file_path = './Winnie_the_Pooh_3_Pages.pdf'
mime_type = 'application/pdf'  # Refer to https://cloud.google.com/document-ai/docs/file-types for supported file types
field_mask = "text,pages.pageNumber"  # Optional. The fields to return in the Document object.


class DocumentAIProcessor:
    def __init__(
            self,
            project_id: str,
            location: str,
            processor_id: str,
            # processor_version: str,
            mime_type: str,
    ):
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id
        # self.processor_version = processor_version
        self.mime_type = mime_type

        # You must set the api_endpoint if you use a location other than 'us'.
        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        self.client = documentai.DocumentProcessorServiceClient(client_options=opts)


    def process_document(self, file_path: str) -> List[str]:
        name = self.client.processor_path(self.project_id, self.location, self.processor_id)

        with open(file_path, "rb") as image:
            image_content = image.read()

        raw_document = documentai.RawDocument(
            content=image_content, mime_type=self.mime_type
        )

        request = documentai.ProcessRequest(name=name, raw_document=raw_document)

        result = self.client.process_document(request=request)

        document = result.document
        page_contents = []

        for page in document.pages:
            page_content = ""
            for paragraph in page.paragraphs:
                paragraph_text = self.layout_to_text(paragraph.layout, document.text)
                page_content += paragraph_text + "\n"
            page_contents.append(page_content.strip())

        return page_contents

    @staticmethod
    def layout_to_text(layout: documentai.Document.Page.Layout, text: str) -> str:
        """
        Document AI identifies text in different parts of the document by their
        offsets in the entirety of the document's text. This function converts
        offsets to a string.
        """
        response = ""
        # If a text segment spans several lines, it will
        # be stored in different text segments.
        for segment in layout.text_anchor.text_segments:
            start_index = int(segment.start_index)
            end_index = int(segment.end_index)
            response += text[start_index:end_index]
        return response

#usage
# processor = DocumentAIProcessor(project_id, location, processor_id, mime_type)
# page_contents = processor.process_document(file_path)
# print(len(page_contents))
# print(page_contents)