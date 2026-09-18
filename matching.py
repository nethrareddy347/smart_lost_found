def calculate_match(lost_item, found_item):

    score = 0

    # Category match
    if lost_item["category"].lower() == found_item["category"].lower():
        score += 30

    # Location match
    if lost_item["location"].lower() == found_item["location"].lower():
        score += 25

    # Item name match
    lost_name = lost_item["name"].lower()
    found_name = found_item["name"].lower()

    if lost_name == found_name:
        score += 30

    elif lost_name in found_name or found_name in lost_name:
        score += 20

    # Description keyword match
    lost_words = set(
        lost_item["description"].lower().split()
    )

    found_words = set(
        found_item["description"].lower().split()
    )

    common_words = lost_words.intersection(found_words)

    if common_words:
        score += 15

    return score


def find_matches(reports, status_map=None):

    matches = []

    if status_map is None:
        status_map = {}

    lost_items = [
        report
        for report in reports
        if report["item_type"] == "lost"
    ]

    found_items = [
        report
        for report in reports
        if report["item_type"] == "found"
    ]

    for lost in lost_items:

        for found in found_items:

            score = calculate_match(
                lost,
                found
            )

            if score >= 40:

                match_id = f"{lost['id']}-{found['id']}"

                matches.append({

    "id": match_id,

    "lost_item": lost["name"],

    "lost_location": lost["location"],

    "lost_photo": lost.get("photo"),

    "found_item": found["name"],

    "found_location": found["location"],

    "found_photo": found.get("photo"),

    "score": score,

    "status": status_map.get(
        match_id,
        "potential"
    )
})

    matches.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return matches