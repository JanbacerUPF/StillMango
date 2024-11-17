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
import random


# Set the environment variable for UTF-8 support
os.environ["PYTHONIOENCODING"] = "utf-8"

# Ensure stdout uses UTF-8
sys.stdout.reconfigure(encoding="utf-8")
def filter_objective(objective: str) -> str:
    # Lowercase and remove non-alphanumeric characters for better matching
    objective = objective.lower()
    
    # Keywords for different objectives
    win_keywords = ['win', 'first prize', 'trophy', 'compete', 'victory']
    learn_keywords = ['learn', 'first time', 'new skills', 'develop', 'experience', 'improve']
    meet_keywords = ['meet', 'network', 'collaborate', 'make friends', 'community']

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


#calculate compatibility score between two participants
def calculate_compatibility(p1, p2):
    score = 0
    
    # Language Compatibility
    if set(p1.preferred_languages).intersection(set(p2.preferred_languages)):
        score += 1
    
    # Objective Compatibility
    if p1.objective == p2.objective:
        score += 1
    
    # Availability Compatibility
    if p1.availability == p2.availability:
        score += 1
    
    # Experience Level Compatibility (only for prize-hunting participants)
    if p1.objective == "prize-hunting" and p1.experience_level == p2.experience_level:
        score += 1

    return score


# Function to assign participants to teams
def form_teams(participants: List[Participant], max_team_size: int) -> List[List[Participant]]:
    random.shuffle(participants)  # Shuffle participants to avoid bias in order
    teams = []
    unassigned = participants.copy()  # Keep track of unassigned participants
    
    # Group participants by their preferred languages
    language_groups = defaultdict(list)
    for participant in participants:
        language_groups[tuple(participant.preferred_languages)].append(participant)
    
    # Group participants by their filtered objectives
    objective_groups = defaultdict(list)
    for participant in participants:
        objective = filter_objective(participant.objective)
        participant.objective = objective  # Update the participant's objective with the filtered one
        objective_groups[objective].append(participant)
    
    # Group participants by filtered interests
    interest_groups = defaultdict(list)
    for participant in participants:
        categorized_interests = filter_interests(participant.interests)
        participant.interests = categorized_interests  # Update the participant's interests
        for interest in categorized_interests:
            interest_groups[interest].append(participant)
    
    # Track which participants have already been assigned to a team
    assigned_participants = set()
    
    # Try to form teams based on language, objective, and interest groups
    for objective_group in objective_groups.values():
        for interest_group in interest_groups.values():
            # Find participants who match both objective and interest
            combined_group = [p for p in objective_group if p in interest_group and p not in assigned_participants]

            # Sort the group by their preferred team size
            combined_group.sort(key=lambda p: p.preferred_team_size)
            
            # Try to form teams based on team size preference
            while len(combined_group) >= max_team_size:
                team = combined_group[:max_team_size]
                teams.append(team)
                for member in team:
                    assigned_participants.add(member)
                combined_group = combined_group[max_team_size:]
            
            # Handle smaller groups or leftover participants
            if combined_group:
                team = combined_group
                teams.append(team)
                for member in team:
                    assigned_participants.add(member)
    
    # Optional: Handle the case where some participants haven't been assigned to any team
    remaining_participants = [p for p in participants if p not in assigned_participants]
    if remaining_participants:
        teams.append(remaining_participants)
    
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
        print(f"Missing participants: {missing_participants}")
        return False
    
    # If all checks pass
    print("\nAll participants are correctly grouped and unique.")
    return True

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


    balanced_teams = form_teams(remaining_participants, TEAM_SIZE)

    all_groups = friend_groups + balanced_teams
    
    reduced_display_teams(all_groups)

    validate_groups(participants,all_groups)


