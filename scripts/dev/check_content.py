import os
from system.data_manager.content_manager import ContentManager


def main() -> None:
    cm = ContentManager()
    print(f"Resolved dir: {cm.content_dir}")
    subjects = cm.get_all_subjects()
    print(f"Subjects ({len(subjects)}): {subjects}")
    for subj in subjects:
        topics = cm.get_all_topics(subj)
        print(f"- {subj} topics ({len(topics)}): {topics[:10]}")


if __name__ == "__main__":
    main() 