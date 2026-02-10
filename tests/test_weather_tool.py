"""
Test script for Weather Tool
Run this to verify the weather tool is working correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.weather_tool import execute_weather_tool, format_weather_response


def test_weather_tool():
    """Test the weather tool with sample questions"""
    
    print("="* 70)
    print("🧪 TESTING WEATHER TOOL")
    print("=" * 70)
    
    test_questions = [
        "What's the weather in London?",
        "Show me temperature in Tokyo",
        "Is it raining in New York?",
        "Weather in Paris",
        "How's the weather in Los Angeles?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {i}/5")
        print(f"{'─' * 70}")
        print(f"📝 Question: {question}")
        print()
        
        # Execute the weather tool
        result = execute_weather_tool(question)
        
        if result["success"]:
            print("✅ Tool execution: SUCCESS")
            print()
            
            # Display raw data
            data = result["data"]
            print(f"📍 Location: {data['city']}, {data['country']}")
            print(f"🌡️  Temperature: {data['temperature']}{data['temp_unit']}")
            print(f"🤔 Feels like: {data['feels_like']}{data['temp_unit']}")
            print(f"💧 Humidity: {data['humidity']}%")
            print(f"💨 Wind: {data['wind_speed']} m/s")
            print(f"{data['icon']} Condition: {data['description'].title()}")
            print()
            
            # Generate natural language response
            nl_response = format_weather_response(data)
            print("🤖 Natural Language Response:")
            print(f"   {nl_response}")
            
        else:
            print("❌ Tool execution: FAILED")
            print(f"   Error: {result['error']}")
    
    print(f"\n{'=' * 70}")
    print("✅ Testing complete!")
    print("=" * 70)


def check_setup():
    """Check if everything is set up correctly"""
    
    print("\n" + "=" * 70)
    print("🔍 CHECKING SETUP")
    print("=" * 70)
    
    errors = []
    
    # Check 1: .env file
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        errors.append("❌ .env file not found. Create it from env_template.txt")
    else:
        print("✅ .env file exists")
    
    # Check 2: API key
    try:
        from config.credentials import CredentialsManager
        creds = CredentialsManager()
        key = creds.get_api_key("openweather")
        print(f"✅ OpenWeather API key loaded: {key[:10]}...")
    except Exception as e:
        errors.append(f"❌ API key problem: {e}")
    
    # Check 3: Dependencies
    try:
        import spacy
        print("✅ spaCy installed")
        
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy model (en_core_web_sm) loaded")
        except:
            errors.append("❌ spaCy model not found. Run: python -m spacy download en_core_web_sm")
    except ImportError:
        errors.append("❌ spaCy not installed")
    
    try:
        import requests
        print("✅ requests library installed")
    except ImportError:
        errors.append("❌ requests library not installed")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        errors.append("❌ python-dotenv not installed")
    
    # Summary
    print("=" * 70)
    if errors:
        print("\n⚠️  SETUP INCOMPLETE:")
        for error in errors:
            print(f"   {error}")
        print("\nPlease fix the issues above before running tests.")
        return False
    else:
        print("\n✅ All checks passed! Ready to test.")
        return True


if __name__ == "__main__":
    print("\n" + "🌤️  WEATHER TOOL TEST SUITE" + "\n")
    
    # Check setup first
    if check_setup():
        # Run tests
        test_weather_tool()
    else:
        print("\n💡 Setup instructions:")
        print("   1. Copy env_template.txt to .env")
        print("   2. Add your OpenWeatherMap API key to .env")
        print("   3. Run: conda env update -f environment.yml --prune")
        print("   4. Run: python -m spacy download en_core_web_sm")
        print("   5. Run this script again")

