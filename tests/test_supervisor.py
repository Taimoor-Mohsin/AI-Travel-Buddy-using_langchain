from src.agents.supervisor import TravelBuddySupervisor

if __name__ == "__main__":
    supervisor = TravelBuddySupervisor()
    user_input = (
        "I'd like to visit Tokyo from September 12th to September 14th. "
        "My budget is around $2000 and I'm interested in anime and traditional food."
    )
    output = supervisor.run(user_input)
    # print("Pipeline output:", output)
