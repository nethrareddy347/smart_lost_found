import os
import torch

from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# AI MODEL CONFIGURATION
# ============================================================

print("Loading AI models...")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading CLIP model...")

clip_model = CLIPModel.from_pretrained(
    "openai/clip-vit-base-patch32"
).to(DEVICE)

clip_processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32"
)

print("Loading text model...")

text_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print(f"AI models loaded on: {DEVICE}")


# ============================================================
# HELPER
# ============================================================

def clamp_score(value):
    """
    Keep a score between 0 and 1.
    """
    return max(0.0, min(1.0, float(value)))


# ============================================================
# IMAGE FEATURE EXTRACTION
# ============================================================

def get_image_features(image):

    inputs = clip_processor(
        images=image,
        return_tensors="pt"
    )

    pixel_values = inputs["pixel_values"].to(DEVICE)

    with torch.no_grad():

        # Get CLIP vision output
        vision_outputs = clip_model.vision_model(
            pixel_values=pixel_values
        )

        # Get pooled image representation
        pooled_output = vision_outputs.pooler_output

        # Project into CLIP embedding space
        image_features = clip_model.visual_projection(
            pooled_output
        )

    # Normalize embedding
    image_features = image_features / image_features.norm(
        dim=-1,
        keepdim=True
    )

    return image_features


# ============================================================
# IMAGE SIMILARITY
# ============================================================

def image_similarity(image1_path, image2_path):

    if not image1_path or not image2_path:
        return 0.0

    if not os.path.isfile(image1_path):
        return 0.0

    if not os.path.isfile(image2_path):
        return 0.0

    try:

        image1 = Image.open(
            image1_path
        ).convert("RGB")

        image2 = Image.open(
            image2_path
        ).convert("RGB")

        # Extract embeddings separately
        features1 = get_image_features(image1)
        features2 = get_image_features(image2)

        # Cosine similarity using normalized vectors
        similarity = torch.sum(
            features1 * features2,
            dim=-1
        ).item()

        # CLIP cosine similarity can technically be negative
        # Convert it into a useful 0-1 score.
        similarity = (similarity + 1.0) / 2.0

        similarity = clamp_score(similarity)

        return similarity

    except Exception as e:

        print(
            "Image similarity error:",
            repr(e)
        )

        return 0.0


# ============================================================
# DESCRIPTION SIMILARITY
# ============================================================

def description_similarity(
    description1,
    description2
):

    if not description1 or not description2:
        return 0.0

    try:

        description1 = str(
            description1
        ).strip()

        description2 = str(
            description2
        ).strip()

        if not description1 or not description2:
            return 0.0

        embeddings = text_model.encode(
            [
                description1,
                description2
            ],
            normalize_embeddings=True
        )

        score = cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]

        # Convert -1..1 to 0..1
        score = (score + 1.0) / 2.0

        return clamp_score(score)

    except Exception as e:

        print(
            "Description similarity error:",
            repr(e)
        )

        return 0.0


# ============================================================
# CATEGORY SIMILARITY
# ============================================================

def category_similarity(
    category1,
    category2
):

    if not category1 or not category2:
        return 0.0

    category1 = str(
        category1
    ).strip().lower()

    category2 = str(
        category2
    ).strip().lower()

    if category1 == category2:
        return 1.0

    return 0.0


# ============================================================
# NAME SIMILARITY
# ============================================================

def name_similarity(
    name1,
    name2
):

    if not name1 or not name2:
        return 0.0

    name1 = str(
        name1
    ).strip().lower()

    name2 = str(
        name2
    ).strip().lower()

    if not name1 or not name2:
        return 0.0

    if name1 == name2:
        return 1.0

    # Partial word matching
    words1 = set(name1.split())
    words2 = set(name2.split())

    if not words1 or not words2:
        return 0.0

    common_words = words1.intersection(
        words2
    )

    if common_words:
        return len(common_words) / max(
            len(words1),
            len(words2)
        )

    return 0.0


# ============================================================
# LOCATION SIMILARITY
# ============================================================

def location_similarity(
    location1,
    location2
):

    if not location1 or not location2:
        return 0.0

    location1 = str(
        location1
    ).strip().lower()

    location2 = str(
        location2
    ).strip().lower()

    if location1 == location2:
        return 1.0

    # Partial location matching
    if (
        location1 in location2
        or location2 in location1
    ):
        return 0.7

    return 0.0


# ============================================================
# AI MATCHING ENGINE
# ============================================================

def find_ai_matches(
    reports,
    upload_folder
):

    lost_items = [
        report
        for report in reports
        if report.get("item_type") == "lost"
    ]

    found_items = [
        report
        for report in reports
        if report.get("item_type") == "found"
    ]

    matches = []

    # --------------------------------------------------------
    # Compare every lost item with every found item
    # --------------------------------------------------------

    for lost in lost_items:

        for found in found_items:

            # =================================================
            # PHOTO PATHS
            # =================================================

            lost_photo = lost.get(
                "photo",
                ""
            )

            found_photo = found.get(
                "photo",
                ""
            )

            lost_photo_path = None
            found_photo_path = None

            if lost_photo:

                lost_photo_path = os.path.join(
                    upload_folder,
                    lost_photo
                )

            if found_photo:

                found_photo_path = os.path.join(
                    upload_folder,
                    found_photo
                )

            # =================================================
            # AI SCORES
            # =================================================

            image_score = image_similarity(
                lost_photo_path,
                found_photo_path
            )

            description_score = description_similarity(
                lost.get("description", ""),
                found.get("description", "")
            )

            category_score = category_similarity(
                lost.get("category", ""),
                found.get("category", "")
            )

            name_score = name_similarity(
                lost.get("name", ""),
                found.get("name", "")
            )

            location_score = location_similarity(
                lost.get("location", ""),
                found.get("location", "")
            )

            # =================================================
            # FINAL MATCH SCORE
            # =================================================

            final_score = (
                image_score * 45
                + description_score * 25
                + category_score * 15
                + location_score * 10
                + name_score * 5
            )

            final_score = round(
                final_score,
                2
            )

            # =================================================
            # MATCH THRESHOLD
            # =================================================

            if final_score < 40:
                continue

            # =================================================
            # MATCH ID
            # =================================================

            match_id = (
                f"{lost['id']}-{found['id']}"
            )

            # =================================================
            # MATCH LABEL
            # =================================================

            if final_score >= 80:

                label = "Strong Match"

            elif final_score >= 65:

                label = "Likely Match"

            else:

                label = "Possible Match"

            # =================================================
            # CREATE MATCH
            # =================================================

            matches.append({

                "id": match_id,

                # -------------------------------
                # LOST ITEM
                # -------------------------------

                "lost_id": lost["id"],

                "lost_item": lost.get(
                    "name",
                    ""
                ),

                "lost_location": lost.get(
                    "location",
                    ""
                ),

                "lost_photo": lost.get(
                    "photo",
                    ""
                ),

                "lost_category": lost.get(
                    "category",
                    ""
                ),

                "lost_description": lost.get(
                    "description",
                    ""
                ),

                # -------------------------------
                # FOUND ITEM
                # -------------------------------

                "found_id": found["id"],

                "found_item": found.get(
                    "name",
                    ""
                ),

                "found_location": found.get(
                    "location",
                    ""
                ),

                "found_photo": found.get(
                    "photo",
                    ""
                ),

                "found_category": found.get(
                    "category",
                    ""
                ),

                "found_description": found.get(
                    "description",
                    ""
                ),

                # -------------------------------
                # SCORES
                # -------------------------------

                "score": final_score,

                "image_score": round(
                    image_score * 100,
                    2
                ),

                "description_score": round(
                    description_score * 100,
                    2
                ),

                "category_score": round(
                    category_score * 100,
                    2
                ),

                "name_score": round(
                    name_score * 100,
                    2
                ),

                "location_score": round(
                    location_score * 100,
                    2
                ),

                # -------------------------------
                # LABEL / STATUS
                # -------------------------------

                "match_label": label,

                "status": "potential"
            })

    # ========================================================
    # SORT BEST MATCHES FIRST
    # ========================================================

    matches.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return matches 