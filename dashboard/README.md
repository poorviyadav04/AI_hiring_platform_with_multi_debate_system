# Streamlit Dashboard

Beautiful, interactive web interface for the AI Hiring Decision Intelligence System.

## 🚀 Quick Start

```bash
# Install dependencies (if not already installed)
pip install streamlit plotly

# Run the dashboard
streamlit run dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## 📋 Features

### 🏠 Home Page
- System overview and statistics
- Feature highlights
- Quick start guide
- Architecture overview

### 👤 Candidate Evaluation
- Select candidate and job position
- Run multi-agent evaluation
- View overall score with gauge chart
- Component breakdown (skills, experience, education, interviews)
- Full debate transcript from all 4 agents
- Real-time LLM integration (when Ollama available)

### 🔍 Counterfactual Explorer
- **Skills**: See impact of adding missing skills
- **Experience**: Test different years of experience
- **Education**: Explore higher education scenarios
- **Salary**: Analyze budget fit scenarios
- Interactive visualizations for what-if analysis

### 🛡️ Red Team Analysis
- Adversarial challenge summary
- Bias detection results
- Boundary testing alerts
- Consistency validation
- Full Red Team report with actionable insights

### 📊 Analytics (Coming Soon)
- Historical decision trends
- Bias pattern detection
- System performance metrics
- Candidate comparison tools

## ⚙️ Settings

**Sidebar Controls:**
- **Enable LLM Agents**: Toggle natural language debates (requires Ollama)
- **Enable Red Team**: Toggle adversarial testing
- **System Status**: Real-time Ollama connection status

## 🎨 UI Features

- **Custom Theme**: Purple gradient design with professional styling
- **Responsive Layout**: Works on desktop and tablet
- **Interactive Charts**: Powered by Plotly
- **Gauge Visualizations**: Real-time score displays
- **Decision Chips**: Color-coded decision indicators
- **Tabbed Interface**: Organized agent debates

## 📸 Screenshots

### Home Page
- System metrics and feature overview
- Quick start guide

### Evaluation Page
- Candidate and job selection
- Real-time evaluation
- Score visualizations
- Debate transcripts

### Counterfactual Explorer
- What-if scenario analysis
- Impact calculations
- Actionable recommendations

### Red Team Dashboard
- Challenge detection
- Risk assessment
- Bias alerts

## 🔧 Customization

### Custom Theme
Edit the CSS in `app.py`:
```python
st.markdown("""
<style>
    .main-header {
        /* Your custom styles */
    }
</style>
""", unsafe_allow_html=True)
```

### Add New Pages
```python
def show_my_new_page():
    st.markdown("## My New Feature")
    # Your code here

# In main():
if page == "🆕 New Page":
    show_my_new_page()
```

## 📦 Dependencies

- **streamlit** - Web framework
- **plotly** - Interactive charts
- **pandas** - Data manipulation
- All project dependencies (from main requirements.txt)

## 🐛 Troubleshooting

**Dashboard won't start:**
```bash
# Reinstall Streamlit
pip install --upgrade streamlit
```

**Ollama not detected:**
- Ensure Ollama is running: `ollama serve`
- Check connection: `curl http://localhost:11434/api/tags`

**Charts not rendering:**
```bash
# Reinstall Plotly
pip install --upgrade plotly
```

## 🚢 Deployment

### Local Development
```bash
streamlit run dashboard/app.py
```

### Production (with Streamlit Cloud)
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Deploy from `dashboard/app.py`

### Docker (see Phase 12)
```bash
docker-compose up dashboard
```

## 📝 Notes

- Session state persists evaluation results
- LLM mode requires Ollama running locally
- Red Team analysis stored in session
- Analytics features coming in future updates

## 🎯 Next Steps

After exploring the dashboard:
1. Try different candidates and jobs
2. Experiment with counterfactual what-if scenarios
3. Review Red Team challenges for biases
4. Check analytics for decision patterns

---

**Built with ❤️ using Streamlit**
