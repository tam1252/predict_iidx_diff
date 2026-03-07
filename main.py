from src.textage.textage_parser import get_score_data
from src.score_analyzer import analyze_density, detect_patterns

url = "https://textage.cc/score/21/verflcht.html?1XC00"
data = get_score_data(url)

density = analyze_density(data)
patterns = detect_patterns(data)

print(density)
print(patterns)