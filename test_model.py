from transformers import pipeline


# MODEL_PATH = "C:/Users/Admin/Desktop/TIC_Project/bert-emotion-recognition"
MODEL_PATH = "C:/Users/Admin/Desktop/TIC_Project/deberta-emotion-recognition"

def main():
    clf = pipeline(
        "text-classification",
        model=MODEL_PATH,
        tokenizer=MODEL_PATH,
        max_length=128,
        truncation=True,
        padding="max_length"
    )

    print("Enter English text to predict emotion (press Enter to exit):")

    while True:
        text = input("\nEnter text: ").strip()
        if not text:
            print("Exited.")
            break

        result = clf(text)[0]
        print(f"Text: {text}")
        print(f"Label: {result['label']} | Score: {result['score']:.4f}")
        print("-" * 40)


if __name__ == "__main__":
    main()
