import requests
from bs4 import BeautifulSoup
from pathlib import Path

URL = "https://vesit.ves.ac.in/"
OUT = Path("data/vesit_general.txt")
OUT.parent.mkdir(exist_ok=True)

print("🌐 Fetching VESIT website...")

r = requests.get(URL, timeout=30)
r.raise_for_status()

soup = BeautifulSoup(r.text, "html.parser")

# Remove junk
for tag in soup(["script", "style", "nav", "footer", "header"]):
    tag.decompose()

text = soup.get_text(separator="\n")

# Clean lines
lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 40]

final_text = "\n".join(lines)

OUT.write_text(final_text, encoding="utf-8")

print("✅ Website text saved to:", OUT)
print("📄 Characters:", len(final_text))

