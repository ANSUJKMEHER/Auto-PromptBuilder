from prompt_engine import generate_prompt #CODE 

def run_chaining(steps, initial_input, temperature=0.7, max_tokens=300):
    all_outputs = []
    current_input = initial_input

    for i, step_prompt in enumerate(steps):
        # Replace placeholder or just append the input
        if "{input}" in step_prompt:
            full_prompt = step_prompt.replace("{input}", current_input)
        else:
            full_prompt = f"{step_prompt.strip()} {current_input}"

        # Call generate_prompt with parameters
        output = generate_prompt(full_prompt, temperature=temperature, max_tokens=max_tokens)

        all_outputs.append((f"Step {i+1}", full_prompt, output))
        current_input = output

    return all_outputs
