from app.database.connection import SessionLocal
from app.models.skill import Skill


technical_skills = [
    "Python",
    "SQL",
    "Power BI",
    "Excel",
    "Tableau",
    "Machine Learning",
    "Java",
    "HTML",
    "CSS",
    "JavaScript",
    "React",
    "Node.js",
    "TypeScript",
    "Git",
    "FastAPI",
]

soft_skills = [
    "Communication",
    "Leadership",
    "Teamwork",
    "Problem Solving",
    "Critical Thinking",
    "Creativity",
    "Time Management",
    "Adaptability",
    "Presentation",
    "Negotiation",
]


def seed_skills():
    db = SessionLocal()

    try:
        for skill_name in technical_skills:
            existing_skill = (
                db.query(Skill)
                .filter(Skill.name == skill_name)
                .first()
            )

            if not existing_skill:
                db.add(
                    Skill(
                        name=skill_name,
                        category="technical",
                    )
                )

        for skill_name in soft_skills:
            existing_skill = (
                db.query(Skill)
                .filter(Skill.name == skill_name)
                .first()
            )

            if not existing_skill:
                db.add(
                    Skill(
                        name=skill_name,
                        category="soft",
                    )
                )

        db.commit()

        print("Skills seeded successfully")

    except Exception as e:
        db.rollback()
        print("Error:", e)

    finally:
        db.close()


if __name__ == "__main__":
    seed_skills()