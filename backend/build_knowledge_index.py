from backend.services.semantic_retriever import career_semantic_retriever

if __name__ == "__main__":
    result = career_semantic_retriever.build_index()
    print("CareerPilot semantic knowledge index built")
    print(f"Sources : {result['sources']}")
    print(f"Chunks  : {result['records']}")
    print(f"Dim     : {result['dimension']}")
    print(f"Model   : {result['model']}")
