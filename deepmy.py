import streamlit as st
import openai

# Set your OpenAI API key in Streamlit secrets or as an environment variable
try:
    openai.api_key = st.secrets["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"]
except KeyError:
    st.error("Please set the OPENAI_API_KEY in Streamlit secrets or environment variables.")
    st.stop()

# Initialize session state variables
if "step" not in st.session_state:
    st.session_state.step = "input"
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "tone" not in st.session_state:
    st.session_state.tone = "Informative"
if "outline" not in st.session_state:
    st.session_state.outline = ""
if "section_index" not in st.session_state:
    st.session_state.section_index = 0
if "sections" not in st.session_state:
    st.session_state.sections = ["Hook", "Introduction", "Main Content", "Engagement", "Conclusion", "CTA"]
if "section_content" not in st.session_state:
    st.session_state.section_content = {}

def generate_outline(topic, tone):
    prompt = f"""
Generate a detailed YouTube video script outline for the topic "{topic}" in a {tone.lower()} tone. 
Include a compelling title at the beginning. Follow this structure:

1. Hook (0-10 sec):
   - Powerful opening line
   - Shocking fact or question

2. Introduction (10-30 sec):
   - Engaging topic introduction
   - Importance explanation

3. Main Content (30 sec - X min):
   - 3 key points with explanations, examples, and visual suggestions

4. Engagement (Throughout):
   - Audience interaction prompts

5. Conclusion (Last 30 sec):
   - Key points summary
   - Next video teaser

6. CTA:
   - Clear subscription/like/share prompts

Provide a well-structured outline with markdown formatting."""
    
    try:
        with st.spinner("Outline generation in progress..."):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.7
            )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Outline generation failed: {str(e)}")
        return ""

def generate_section(topic, section_name, tone):
    prompt = f"""
Generate a detailed script section for "{section_name}" of a YouTube video about "{topic}" in {tone.lower()} tone. 

Focus on:
- { "Attention-grabbing opener" if section_name == "Hook" else ""}
- { "Clear topic setup" if section_name == "Introduction" else ""}
- { "Detailed examples & visuals" if section_name == "Main Content" else ""}
- { "Audience interaction" if section_name == "Engagement" else ""}
- { "Memorable summary" if section_name == "Conclusion" else ""}
- { "Strong action prompts" if section_name == "CTA" else ""}

Provide 3-5 concise paragraphs with markdown formatting where appropriate."""
    
    try:
        with st.spinner(f"Generating {section_name} section..."):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Section generation failed: {str(e)}")
        return ""

# Step 1: Initial Input
if st.session_state.step == "input":
    st.title("YouTube Script Wizard 🧙♂️")
    st.write("आपके YouTube वीडियो का विषय और टोन चुनें:")
    
    topic_input = st.text_input("वीडियो का विषय", key="topic_input")
    tone = st.selectbox("टोन चुनें", ["Informative", "Casual", "Humorous", "Motivational"], key="tone_select")
    
    if st.button("आउटलाइन बनाएं"):
        if not topic_input.strip():
            st.error("कृपया एक वैध विषय दर्ज करें")
        else:
            st.session_state.topic = topic_input
            st.session_state.tone = tone
            st.session_state.outline = generate_outline(topic_input, tone)
            st.session_state.step = "outline_confirm"
            st.rerun()

# Step 2: Outline Confirmation
if st.session_state.step == "outline_confirm":
    st.title("आउटलाइन समीक्षा")
    st.subheader("जनरेटेड आउटलाइन")
    st.markdown(st.session_state.outline)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("नया आउटलाइन बनाएं"):
            st.session_state.outline = generate_outline(st.session_state.topic, st.session_state.tone)
            st.rerun()
    with col2:
        if st.button("स्क्रिप्ट बनाना जारी रखें"):
            st.session_state.step = "section"
            st.session_state.section_index = 0
            st.rerun()

# Step 3: Section Generation
if st.session_state.step == "section":
    current_index = st.session_state.section_index
    if current_index < len(st.session_state.sections):
        current_section = st.session_state.sections[current_index]
        st.title(f"अध्याय: {current_section}")
        
        if current_section not in st.session_state.section_content:
            st.session_state.section_content[current_section] = generate_section(
                st.session_state.topic, current_section, st.session_state.tone
            )
        
        st.markdown(st.session_state.section_content[current_section])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"पुनः जनरेट करें", key=f"regen_{current_section}"):
                st.session_state.section_content[current_section] = generate_section(
                    st.session_state.topic, current_section, st.session_state.tone
                )
                st.rerun()
        with col2:
            if st.button("अगला अध्याय", key=f"next_{current_section}"):
                st.session_state.section_index += 1
                st.rerun()
    else:
        # Final Script Display
        st.title("🎉 पूरी स्क्रिप्ट तैयार है!")
        final_script = f"# {st.session_state.topic}\n\n"
        for section in st.session_state.sections:
            final_script += f"## {section}\n{st.session_state.section_content.get(section, '')}\n\n"
        
        st.markdown(final_script)
        
        # Download button
        st.download_button(
            label="स्क्रिप्ट डाउनलोड करें",
            data=final_script,
            file_name=f"{st.session_state.topic.replace(' ', '_')}_script.md",
            mime="text/markdown"
        )
        
        if st.button("नई स्क्रिप्ट बनाएं"):
            st.session_state.clear()
            st.rerun()