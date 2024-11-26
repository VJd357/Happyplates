class MenuPrompt:
    @staticmethod
    def get_prompt_full_menu():
        return f"""
        Extract comprehensive menu information in JSON format from the given complete menu image.
        The output JSON should be structured to include multiple sections, each with its own item type and corresponding items. Each section should be represented as follows:
        - "item_type": The heading of the section, representing the category of items.
        - "items": A list of items within this section, where each item contains:
          - "item_name": The name of the item.
          - "item_description": A detailed description of the item, if available.
          - "item_price": The price of the item, if listed.
          - "item_portion": The portion size of the item, if mentioned.

        The JSON should be organized to facilitate easy conversion into a DataFrame format, allowing for clear differentiation between sections and their respective items.

        Example:
        [
            {{
                "item_type": "OUR FAVORITE SANDWICHES",
                "items": [
                    {{
                        "item_name": "TIJUANA CHICKEN SANDWICH",
                        "item_description": "Fresh breast of chicken, pounded thin, broiled & served with lettuce & tomato under melted Jalapeno cheese on a roll.",
                        "item_price": "$5.75",
                        "item_portion": null
                    }},
                    {{
                        "item_name": "BASIC CHICKEN SANDWICH",
                        "item_description": "Boneless breast of chicken, broiled plain and served on your choice of breads or hard roll.",
                        "item_price": null,
                        "item_portion": null
                    }}
                ]
            }},
            {{
                "item_type": "BEVERAGES",
                "items": [
                    {{
                        "item_name": "COFFEE",
                        "item_description": "Freshly brewed coffee.",
                        "item_price": "$2.00",
                        "item_portion": "12 oz"
                    }},
                    {{
                        "item_name": "ICED TEA",
                        "item_description": "Chilled iced tea with lemon.",
                        "item_price": "$2.50",
                        "item_portion": "16 oz"
                    }}
                ]
            }}
        ]
        """

    @staticmethod
    def get_system_prompt():
        return (
            "You are a highly skilled data analyst with over 30 years of experience, "
            "specializing in the restaurant industry. Your extensive expertise includes "
            "analyzing and understanding the structures of thousands of diverse menu types. "
            "Your task is to extract and organize menu information into a structured JSON format, "
            "ensuring accuracy and clarity in the representation of item types, names, descriptions, "
            "prices, and portion sizes."
        )