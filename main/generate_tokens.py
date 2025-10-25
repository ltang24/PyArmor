import secrets, json

def generate_tokens(n=100):
    tokens = [secrets.token_hex(16) for _ in range(n)]
    with open("active_tokens.json", "w") as f:
        json.dump(tokens, f, indent=2)
    print(f"✅ Generated {n} tokens -> active_tokens.json")

if __name__ == "__main__":
    generate_tokens()
