# This program calculates the factorial of a given number

def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

# Get input from the user
number = int(input("Enter a number: "))

# Calculate the factorial of the number
result = factorial(number)

# Display the result
print("The factorial of", number, "is", result)
