from rich import print
from typing import List, Dict
from dataclasses import dataclass
from typing import Literal
import pathlib
import uuid
import json

import sys
import os

# Set the environment variable for UTF-8 support
os.environ["PYTHONIOENCODING"] = "utf-8"

# Ensure stdout uses UTF-8
sys.stdout.reconfigure(encoding="utf-8")


# Participant class
@dataclass
class Participant:
    id: uuid.UUID  # Unique identifier

    # Personal data
    name: str
    email: str
    age: int
    year_of_study: Literal["1st year", "2nd year", "3rd year", "4th year", "Masters", "PhD"]
    shirt_size: Literal["S", "M", "L", "XL"]
    university: str
    dietary_restrictions: Literal["None", "Vegetarian", "Vegan", "Gluten-free", "Other"]

    # Experience and programming skills
    programming_skills: Dict[str, int]
    experience_level: Literal["Beginner", "Intermediate", "Advanced"]
    hackathons_done: int

    # Interests, preferences and constraints
    interests: List[str]
    preferred_role: Literal[
        "Analysis", "Visualization", "Development", "Design", "Don't know", "Don't care"
    ]
    objective: str
    interest_in_challenges: List[str]
    preferred_languages: List[str]
    friend_registration: List[uuid.UUID]
    preferred_team_size: int
    availability: Dict[str, bool]

    # Description of the participant
    introduction: str
    technical_project: str
    future_excitement: str
    fun_fact: str


# Load participants function
def load_participants(path: str) -> List[Participant]:
    if not pathlib.Path(path).exists():
        raise FileNotFoundError(
            f"The file {path} does not exist, are you sure you're using the correct path?"
        )
    if not pathlib.Path(path).suffix == ".json":
        raise ValueError(
            f"The file {path} is not a JSON file, are you sure you're using the correct file?"
        )

    return [Participant(**participant) for participant in json.load(open(path, encoding="utf-8"))]


# Compatibility scoring function
def compatibility_score(participant1: Participant, participant2: Participant) -> int:
    score = 0

    # Shared languages
    shared_languages = set(participant1.preferred_languages) & set(participant2.preferred_languages)
    score += len(shared_languages)

    # Shared interests
    shared_interests = set(participant1.interests) & set(participant2.interests)
    score += len(shared_interests)

    # Shared skills
    shared_skills = set(participant1.programming_skills.keys()) & set(participant2.programming_skills.keys())
    score += sum(
        min(participant1.programming_skills[skill], participant2.programming_skills[skill])
        for skill in shared_skills
    )

    # Shared availability
    shared_availability = sum(
        participant1.availability[time] and participant2.availability[time]
        for time in participant1.availability
    )
    score += shared_availability

    # Objective similarity (non-empty comparison)
    if participant1.objective and participant2.objective:
        score += 1

    return score


# Filtering functions based on keywords (Objective, Interests, Preferred Role)
def filter_objective(objective: str) -> str:
    # Keywords for different objectives
    win_keywords = ['win', 'first prize', 'trophy', 'compete', 'victory']
    learn_keywords = ['learn', 'first time', 'new skills', 'develop', 'experience', 'improve']
    meet_keywords = ['meet', 'network', 'collaborate', 'make friends', 'community']

    # Check for matching keywords and return the category
    objective = objective.lower()
    if any(keyword in objective for keyword in win_keywords):
        return "prize-hunting"
    elif any(keyword in objective for keyword in learn_keywords):
        return "learning new skills"
    elif any(keyword in objective for keyword in meet_keywords):
        return "meeting new people"
    else:
        return "other"


def filter_interests(interests: List[str]) -> List[str]:
    # Keywords for common interest categories
    tech_interests = ['AI', 'machine learning', 'data science', 'programming', 'development']
    design_interests = ['design', 'UI/UX', 'product design', 'web design']
    business_interests = ['business', 'finance', 'startup', 'marketing']

    # Categorize based on interest matches
    categorized_interests = []
    for interest in interests:
        if any(keyword in interest.lower() for keyword in tech_interests):
            categorized_interests.append('Tech')
        elif any(keyword in interest.lower() for keyword in design_interests):
            categorized_interests.append('Design')
        elif any(keyword in interest.lower() for keyword in business_interests):
            categorized_interests.append('Business')
        else:
            categorized_interests.append('Other')

    return categorized_interests


def filter_preferred_role(preferred_role: str) -> str:
    # Define role categories and keywords
    development_roles = ['development', 'developer', 'coding', 'programming']
    design_roles = ['design', 'designer', 'UI/UX', 'graphic design']
    analysis_roles = ['analysis', 'analyst', 'data analysis', 'data science']
    visualization_roles = ['visualization', 'visual', 'dashboard', 'graphics']

    # Match preferred roles to categories
    if any(keyword in preferred_role.lower() for keyword in development_roles):
        return "Development"
    elif any(keyword in preferred_role.lower() for keyword in design_roles):
        return "Design"
    elif any(keyword in preferred_role.lower() for keyword in analysis_roles):
        return "Analysis"
    elif any(keyword in preferred_role.lower() for keyword in visualization_roles):
        return "Visualization"
    else:
        return "Other"


# Create balanced teams
def create_balanced_teams(participants: List[Participant], team_size: int) -> List[List[Participant]]:
    # Separate participants based on preferred team sizes, ensuring a group for preference 0
    preferred_sizes = {1: [], 2: [], 3: [], 4: [], 0: []}  # Include 0 for those with no preference
    for participant in participants:
        preferred_sizes[participant.preferred_team_size].append(participant)

    # Helper function to build teams based on preferences
    def build_teams_from_group(preference_group: List[Participant], max_team_size: int):
        teams = []
        while preference_group:
            team = []
            for _ in range(max_team_size):
                if preference_group:
                    team.append(preference_group.pop())
            teams.append(team)
        return teams

    teams = []
    
    # First, build teams for those who prefer size 4, then 3, 2, and 1
    for size in [4, 3, 2, 1]:
        teams.extend(build_teams_from_group(preferred_sizes[size], size))

    # Now, handle people with preference 0 by grouping them to maximize team preference matches
    all_remaining = preferred_sizes[0] + preferred_sizes[1] + preferred_sizes[2] + preferred_sizes[3]
    teams.extend(build_teams_from_group(all_remaining, 3))  # Default to 3 people for optimization
    
    return teams


# Display teams
def display_teams(teams: List[List[Participant]]):
    for i, team in enumerate(teams, 1):
        print(f"\n[bold]Team {i}[/bold]:")
        for member in team:
            print(f"  - [bold]{member.name}[/bold] (Preferred Team Size: {member.preferred_team_size}, "
                  f"Role: {member.preferred_role_category}, "
                  f"Objective: {member.objective_category}, "
                  f"Experience: {member.experience_level}, "
                  f"Interests: {', '.join(member.interests_category)})")
            print(f"    - University: {member.university}, "
                  f"Year of Study: {member.year_of_study}, "
                  f"Shirt Size: {member.shirt_size}, "
                  f"Skills: {', '.join(member.programming_skills.keys())}")
            print(f"    - Dietary Restrictions: {member.dietary_restrictions}\n")
        print()


# Main execution
if __name__ == "__main__":
    # Path to the data file
    data_path = "data/datathon_participants.json"
    participants = load_participants(data_path)

    # Apply filters to participants' attributes (Objective, Interests, Preferred Role)
    for participant in participants:
        participant.objective_category = filter_objective(participant.objective)
        participant.interests_category = filter_interests(participant.interests)
        participant.preferred_role_category = filter_preferred_role(participant.preferred_role)

    # Print first participant for verification
    print(participants[0])

    # Set team size
    TEAM_SIZE = 4

    # Create teams and display
    balanced_teams = create_balanced_teams(participants, TEAM_SIZE)
    display_teams(balanced_teams)
