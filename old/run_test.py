import test_supabase_connection
import sys

# Redirect stdout to a file
with open('test_output.txt', 'w') as f:
    # Save the original stdout
    original_stdout = sys.stdout
    # Set stdout to the file
    sys.stdout = f
    
    # Run the test
    test_supabase_connection.test_supabase_connection()
    
    # Restore stdout
    sys.stdout = original_stdout

print("Test completed. Check test_output.txt for results.")
