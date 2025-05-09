from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer


class Scrape:
    def __init__(self) -> None:
        pass

    def scrape(self, urls):
        loader = AsyncChromiumLoader(urls)
        docs = loader.load()
        bs_transformer = BeautifulSoupTransformer()
        docs_transformed = bs_transformer.transform_documents(
            docs, tags_to_extract=["span", "p", "li", "article", "h1", "h2", "h3", "h4"]
        )
        return docs_transformed
