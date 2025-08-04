import streamlit as st

# Set the title of the app
st.title("Simple Streamlit App")

# Add a text input widget
user_input = st.text_input("Enter some text:")

# Display the user input
if user_input:
    st.write(f"You entered: {user_input}")

# Add a slider widget
slider_value = st.slider("Select a value:", 0, 100, 50)

# Display the slider value
st.write(f"Slider value: {slider_value}")

# Add a button
if st.button("Click Me"):
    st.write("Button clicked!")