import random
import uuid
from collections import defaultdict
from typing import List, Dict
from dataclasses import dataclass
from typing_extensions import Literal
import re
from participant import Participant, load_participants


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



def main():
    participants = load_participants("data/datathon_participants.json")
    
    # Set the max team size
    max_team_size = 4

    # Create teams based on the given criteria
    teams = form_teams(participants, max_team_size)

    # Display the teams (You can limit the number of teams printed)
    print(f"Total teams formed: {len(teams)}")
    for idx, team in enumerate(teams[:len(teams)]):  # Limit to printing first 5 teams
        print(f"Team {idx + 1}:")
        for participant in team:
            print(f"- {participant.name} (Objective: {participant.objective})")
        print()



if __name__ == "__main__":
    main()
