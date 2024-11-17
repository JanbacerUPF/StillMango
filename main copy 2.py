from collections import defaultdict, Counter
from typing import List

# Participant class definition
class Participant:
    def __init__(self, name, preferred_languages, experience_level, year_of_study, preferred_team_size, preferred_role,
                 objective, interests, university, shirt_size, programming_skills, dietary_restrictions):
        self.name = name
        self.preferred_languages = preferred_languages
        self.experience_level = experience_level
        self.year_of_study = year_of_study
        self.preferred_team_size = preferred_team_size
        self.preferred_role = preferred_role
        self.objective = objective
        self.interests = interests
        self.university = university
        self.shirt_size = shirt_size
        self.programming_skills = programming_skills
        self.dietary_restrictions = dietary_restrictions

# Function to load participants (simulated here as a placeholder)
def load_participants(data_path: str) -> List[Participant]:
    # Replace with actual code to load participant data (e.g., from a JSON file)
    return []

# Create language groups by rarity
def create_language_groups_by_rarity(participants: List[Participant]) -> List[List[Participant]]:
    language_counts = Counter(language for participant in participants for language in participant.preferred_languages)
    sorted_languages = sorted(language_counts, key=language_counts.get)

    language_groups = []
    used_participants = set()

    for language in sorted_languages:
        group = []
        for participant in participants:
            if participant not in used_participants and language in participant.preferred_languages:
                group.append(participant)
                used_participants.add(participant)

        if group:
            language_groups.append(group)

    # Add participants without language preferences to a separate group
    no_language_group = [participant for participant in participants if participant not in used_participants]
    if no_language_group:
        language_groups.append(no_language_group)

    return language_groups

# Create experience and study level groups
def create_experience_and_study_level_groups(participants: List[Participant]) -> List[List[Participant]]:
    experience_groups = defaultdict(list)
    study_groups = defaultdict(list)

    for participant in participants:
        experience_groups[participant.experience_level].append(participant)
        study_groups[participant.year_of_study].append(participant)

    final_groups = []
    for experience in experience_groups:
        for study_year in study_groups:
            common_participants = set(experience_groups[experience]) & set(study_groups[study_year])
            if common_participants:
                final_groups.append(list(common_participants))

    return final_groups

# Create skill-based groups
def create_skill_based_groups(participants: List[Participant]) -> List[List[Participant]]:
    skill_groups = defaultdict(list)
    for participant in participants:
        for skill in participant.programming_skills.keys():
            skill_groups[skill].append(participant)

    return list(skill_groups.values())

# Create balanced teams based on preferred team sizes
def create_balanced_teams(participants: List[Participant], team_size: int) -> List[List[Participant]]:
    preferred_sizes = {i: [] for i in range(team_size, 0, -1)}

    for participant in participants:
        preferred_sizes[participant.preferred_team_size].append(participant)

    def build_teams_from_group(preference_group: List[Participant], max_team_size: int):
        teams = []
        while len(preference_group) >= max_team_size:
            team = [preference_group.pop() for _ in range(max_team_size)]
            teams.append(team)
        return teams

    teams = []
    for size in range(team_size, 0, -1):
        teams.extend(build_teams_from_group(preferred_sizes[size], size))

    leftover_participants = sum(preferred_sizes.values(), [])
    if leftover_participants:
        teams.extend(build_teams_from_group(leftover_participants, team_size))

    return teams

# Main function to process the teams
def create_teams_with_filters(participants: List[Participant], team_size: int) -> List[List[Participant]]:
    # Group participants by language, experience, and skill level
    language_groups = create_language_groups_by_rarity(participants)
    experience_and_study_groups = create_experience_and_study_level_groups(participants)
    skill_groups = create_skill_based_groups(participants)

    # Combine all groups together
    all_groups = language_groups + experience_and_study_groups + skill_groups

    # Create teams based on all groupings
    balanced_teams = create_balanced_teams(sum(all_groups, []), team_size)

    return balanced_teams

# Display the teams with details
def display_teams(teams: List[List[Participant]]):
    for i, team in enumerate(teams, 1):
        print(f"\n[bold]Team {i}[/bold]:")
        for member in team:
            print(f"  - [bold]{member.name}[/bold] (Preferred Team Size: {member.preferred_team_size}, "
                  f"Role: {member.preferred_role}, "
                  f"Objective: {member.objective}, "
                  f"Experience: {member.experience_level}, "
                  f"Interests: {', '.join(member.interests)})")
            print(f"    - University: {member.university}, "
                  f"Year of Study: {member.year_of_study}, "
                  f"Shirt Size: {member.shirt_size}, "
                  f"Skills: {', '.join(member.programming_skills.keys())}")
            print(f"    - Dietary Restrictions: {member.dietary_restrictions}\n")
        print()

# Main execution
if __name__ == "__main__":
    data_path = "data/datathon_participants.json"
    participants = load_participants(data_path)

    TEAM_SIZE = 4  # Set team size for balanced teams

    # Create teams with all filters applied
    all_groups = create_teams_with_filters(participants, TEAM_SIZE)

    # Display teams
    display_teams(all_groups)
