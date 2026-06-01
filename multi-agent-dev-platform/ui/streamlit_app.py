import streamlit as st
import requests

st.title("Multi-Agent Software Builder")

req = st.text_area("Enter Requirement")

if st.button("Run Agents"):
    with st.spinner("Generating project..."):
        try:
            response = requests.post(
                "http://localhost:8000/run-workflow",
                json={"requirement": req},
            )
            
            # Check if response is successful
            if response.status_code != 200:
                st.error(f"❌ API Error: {response.status_code}")
                st.write(response.text)  # Show actual error
            else:
                result = response.json()
                
                if result.get("status") == "completed":
                    st.success("✅ Project Generated Successfully!")
                    st.subheader(f"📦 {result['project_name']}")
                    st.write(f"Path: {result['generated_path']}")
                    st.write(f"ZIP: {result['zip_file']}")

                    with open(result["zip_file"], "rb") as f:
                        st.download_button(
                            label="Download Project ZIP",
                            data=f,
                            file_name="generated-project.zip",
                            mime="application/zip"
                        )
                else:
                    st.error("❌ Project generation failed")
                    st.write(result)
                    
        except requests.exceptions.JSONDecodeError:
            st.error("❌ Backend returned invalid response. Check FastAPI logs.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")