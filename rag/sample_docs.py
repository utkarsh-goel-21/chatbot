from rag.embedder import embed_documents

sample_documents = [
    {
        "id": "doc1",
        "text": "In Q1 2026 our business saw strong growth in electronics category. Laptops and headphones were the top selling products. Revenue increased by 20% compared to last quarter."
    },
    {
        "id": "doc2",
        "text": "Our return rate in March 2026 was very low at 2%. Customer satisfaction scores were high. Most complaints were related to delivery delays not product quality."
    },
    {
        "id": "doc3",
        "text": "Payment trends show that credit card is the most preferred payment method followed by UPI. Cash transactions are declining month over month."
    }
]

if __name__ == "__main__":
    embed_documents(sample_documents)
