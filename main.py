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
from collections import Counter


# Set the environment variable for UTF-8 support
os.environ["PYTHONIOENCODING"] = "utf-8"

# Ensure stdout uses UTF-8
sys.stdout.reconfigure(encoding="utf-8")

#check if programing_skills is valid (1-5)
def fix_programming_language(participants: list) -> None:
    for participant in participants:
        for skill, level in participant.programing_skills.items():
            if level > 5:
                participant.programming_skills[skill] = 5

# compute a score based on compatibility
def compatibility_score(participant1: Participant, participant2: Participant) -> int:
    score = 0

    # Shared skills
    shared_skills = set(participant1.programming_skills.keys()) & set(participant2.programming_skills.keys())
    score += 4*sum(
        min(participant1.programming_skills[skill], participant2.programming_skills[skill])
        for skill in shared_skills
    )

    # Shared availability
    shared_availability = sum(
        participant1.availability[time] and participant2.availability[time]
        for time in participant1.availability
    )
    score += 7*shared_availability

    # Shared experience or different but higher doesnt want to win
    if (participant1.experience_level == participant2.experience_level):
        score += 20
    elif (participant1.experience_level > participant2.experience_level & categorize_objective(participant1.objective) != "prize-hunting"):
        score += 17


    # Different role
    if (participant1.preferred_role != participant2.preferred_role):
        score += 26

    # Hackathons done
    score += 5*(min(participant1.hackathons_done, participant2.hackathons_done))
    

    return score

def create_language_groups_by_rarity(participants: List[Participant]) -> List[List[Participant]]:
    # Count the rarity of each language
    language_counts = Counter(
        language
        for participant in participants
        for language in participant.preferred_languages
    )
    
    # Sort languages by rarity (ascending order)
    sorted_languages = sorted(language_counts, key=language_counts.get)

    language_groups = []
    used_participants = set()

    # Create groups starting with the rarest language
    for language in sorted_languages:
        group = []
        for participant in participants:
            if participant not in used_participants and language in participant.preferred_languages:
                group.append(participant)
                used_participants.add(participant)
        
        # Add the group if not empty
        if group:
            language_groups.append(group)
    
    # Handle participants without languages
    no_language_group = [
        participant for participant in participants if participant not in used_participants
    ]
    if no_language_group:
        language_groups.append(no_language_group)

    return language_groups

    


def categorize_objective(objective: str) -> str:
    # Keywords for different objectives
    win_keywords = ['win', 'winning', 'victory', 'prize', 'trophy', 'competition', 'compete', 
                    'champion', 'beat others', 'best', 'success', 'first place', 'achieve']
    learn_keywords = ['learn', 'learning', 'develop', 'improve', 'skills', 'experience', 
                      'new knowledge', 'practice', 'try new things', 'experiment', 
                      'understand', 'educate', 'growth']
    meet_keywords = ['meet', 'network', 'collaborate', 'connect', 'team up', 'friends', 
                     'make connections', 'community', 'share ideas', 'partner', 'engage', 
                     'interact','blast','buddies']
    negation_words = ['not', "don't", 'never', 'no']

    # Normalize the objective to lowercase for matching
    objective = objective.lower()

    # Check for negations
    def is_negated(keyword: str, text: str) -> bool:
        words = text.split()
        if keyword in words:
            keyword_index = words.index(keyword)
            # Check for negation words within a 3-word range before the keyword
            for i in range(max(0, keyword_index - 3), keyword_index):
                if words[i] in negation_words:
                    return True
        return False

    # Check for each category while avoiding negations
    for keyword in win_keywords:
        if keyword in objective and not is_negated(keyword, objective):
            return "prize-hunting"
    for keyword in learn_keywords:
        if keyword in objective and not is_negated(keyword, objective):
            return "learning new skills"
    for keyword in meet_keywords:
        if keyword in objective and not is_negated(keyword, objective):
            return "meeting new people"

    return "other"


def create_objective_subgroups(language_groups: List[List[Participant]]) -> List[List[Participant]]:
    objective_subgroups = []

    # Process each language group
    for group in language_groups:
        # Subgroups for each objective
        prize_hunting_group = []
        learning_group = []
        meeting_group = []
        other_group = []

        for participant in group:
            category = categorize_objective(participant.objective)
            if category == "prize-hunting":
                prize_hunting_group.append(participant)
            elif category == "learning new skills":
                learning_group.append(participant)
            elif category == "meeting new people":
                meeting_group.append(participant)
            else:
                other_group.append(participant)
        
        # Add non-empty subgroups to the result
        if prize_hunting_group:
            objective_subgroups.append(prize_hunting_group)
        if learning_group:
            objective_subgroups.append(learning_group)
        if meeting_group:
            objective_subgroups.append(meeting_group)
        if other_group:
            objective_subgroups.append(other_group)

    return objective_subgroups


# Create balanced teams
def create_balanced_teams(participants: List[List[Participant]], team_size: int) -> List[List[Participant]]:
    # Separate participants based on preferred team sizes, ensuring a group for preference 0
    preferred_sizes = {1: [], 2: [], 3: [], 4: [], 0: []}  # Include 0 for those with no preference
    for team in participants:
        for participant in team:
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

def create_teams(participants: List[Participant], team_size: int) -> List[List[Participant]]:

    # Create friend groups and remove the used participants from the list
    friend_groups, remaining_participants = create_friend_groups(participants)

    groups=create_language_groups_by_rarity(remaining_participants)

    groups = create_objective_subgroups(groups)

    groups=create_balanced_teams(groups,4)


    teams = friend_groups+groups

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

def reduced_display_teams_limit(teams: List[List[Participant]],number):
    for i, team in enumerate(teams, 1):
        if len(team) == number:
            print(f"\n[bold]Team {i}[/bold]:")
            for member in team:
                print(f"  - [bold]{member.name}[/bold] (Preferred Team Size: {member.preferred_team_size}", end = " ")

def reduced_display_teams(teams: List[List[Participant]]):
    for i, team in enumerate(teams, 1):
        print(f"\n[bold]Team {i}[/bold]:")
        print(categorize_objective(team[0].objective))
        for member in team:
            print(f"  - [bold]{member.name}[/bold]", end = " ")



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

def validate_groups(participants: List[Participant], all_groups: List[List[Participant]]):
    # Step 1: Flatten the list of groups and extract all participants
    all_participants_in_groups = [member for group in all_groups for member in group]
    
    # Step 2: Check for duplicates
    participants_set = set(participants)  # Create a set of all participants for comparison
    all_participants_in_groups_set = set(all_participants_in_groups)  # Set of all participants in groups
    
    if len(all_participants_in_groups) != len(all_participants_in_groups_set):
        print("There are duplicate participants in the groups!")
        return False
    
    # Step 3: Check if any participant is missing from the groups
    if participants_set != all_participants_in_groups_set:
        print("Some participants are missing from the groups!")
        missing_participants = participants_set - all_participants_in_groups_set
        for member in missing_participants:
            print(f"Missing participants: {member.name}")
        return False
    
    # If all checks pass
    print("\nAll participants are correctly grouped and unique.")
    return True

# Main execution
if __name__ == "__main__":
    # Path to the data file
    data_path = "data/datathon_participants.json"
    participants = load_participants(data_path)

    """# Create friend groups and remove the used participants from the list
    friend_groups, remaining_participants = create_friend_groups(participants)

    # Display the friend groups
    for i, group in enumerate(friend_groups, 1):

        print(f"Friend Group {i}:")
        for member in group:
            print(f"  - {member.name} (ID: {member.id})")
    """

    # Set team size for balanced teams
    TEAM_SIZE = 4


    """balanced_teams = create_balanced_teams(remaining_participants, TEAM_SIZE)

    all_groups = friend_groups + balanced_teams"""

    all_groups = create_teams(participants, TEAM_SIZE)
    
    reduced_display_teams(all_groups)

    validate_groups(participants,all_groups)


