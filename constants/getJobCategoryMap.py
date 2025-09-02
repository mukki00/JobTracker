JOB_CATEGORY_MAP = {
    "recommended": "Recommended",
    "easy-apply": "Easy Apply",
    "remote-jobs": "Remote",
    "it-services-and-it-consulting": "IT",
    "human-resources": "HR",
    "financial-services": "Finance",
    "sustainability": "Sustainability",
    "hybrid": "Hybrid",
    "pharmaceuticals": "Pharma",
    "part-time-jobs": "Part-time",
    "social-impact": "Social impact",
    "manufacturing": "Manufacturing",
    "real-estate": "Real estate",
    "hospitals-and-healthcare": "Healthcare",
    "government": "Government",
    "biotechnology": "Biotech",
    "defense-and-space": "Defense and space",
    "operations": "Operations",
    "construction": "Construction",
    "small-business": "Small biz",
    "human-services": "Human services",
    "publishing": "Publishing",
    "retail": "Retail",
    "hospitality": "Hospitality",
    "education": "Education",
    "media": "Media",
    "restaurants": "Restaurants",
    "transportation-and-logistics": "Logistics",
    "digital-security": "Digital security",
    "marketing-and-advertising": "Marketing",
    "career-growth": "Career growth",
    "higher-edu": "Higher ed",
    "food-and-beverages": "Food & bev",
    "non-profits": "Non-profit",
    "gaming": "Gaming",
    "staffing-and-recruiting": "Recruiting",
    "veterinary-medicine": "Veterinary med",
    "civil-eng": "Civil eng",
    "work-life-balance": "Work-life balance",
    "apparel-and-fashion": "Fashion"
}

def get_job_category(url):
    for key, value in JOB_CATEGORY_MAP.items():
        if key in url:
            return value
    return "recommended"