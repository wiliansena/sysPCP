from app import create_app

app = create_app()


if __name__ == "__main__":
    # Execute o Flask permitindo conexões externas
    app.run(host="0.0.0.0", port=5021)