from rich import print
from typing import List, Dict
from dataclasses import dataclass
from typing import Literal
import pathlib
import uuid
import json
from participant import Participant
from participant import load_participants
import sys
import os
from collections import defaultdict


# Set the environment variable for UTF-8 support
os.environ["PYTHONIOENCODING"] = "utf-8"

# Ensure stdout uses UTF-8
sys.stdout.reconfigure(encoding="utf-8")



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



def create_friend_groups(participants: List[Participant]) -> List[List[Participant]]:
    # Create a dictionary to map participant IDs to their corresponding participants
    participant_map = {participant.id: participant for participant in participants}
    
    # List to store the friend groups formed
    friend_groups = []
    
    # Set to keep track of participants who have already been assigned to a group
    used_ids = set()

    # Loop through participants to form friend groups based on friend_registration
    for participant in participants:
        if participant.id not in used_ids and participant.friend_registration:
            # Start a new group with this participant
            group = [participant]
            used_ids.add(participant.id)
            
            # Add friends from the friend_registration list to the group
            for friend_id in participant.friend_registration:
                # If the friend_id exists in the participant map and is not already in the group
                if friend_id in participant_map and friend_id not in used_ids:
                    friend = participant_map[friend_id]
                    group.append(friend)
                    used_ids.add(friend_id)
            
            # Add the formed group to the friend_groups list
            friend_groups.append(group)
    
    # Remove the participants in friend_groups from the main participants list
    remaining_participants = [p for p in participants if p.id not in used_ids]
    
    # Return the friend groups and the remaining participants
    return friend_groups, remaining_participants



# Main execution
if __name__ == "__main__":
    # Path to the data file
    data_path = "data/datathon_participants.json"
    participants = load_participants(data_path)

    # Create friend groups and remove the used participants from the list
    friend_groups, remaining_participants = create_friend_groups(participants)

    # Display the friend groups
    for i, group in enumerate(friend_groups, 1):

        print(f"Friend Group {i}:")
        for member in group:
            print(f"  - {member.name} (ID: {member.id})")

    # Set team size for balanced teams
    TEAM_SIZE = 4


    balanced_teams = create_balanced_teams(remaining_participants, TEAM_SIZE)

    all_groups = friend_groups + balanced_teams
    display_teams(all_groups)


