def detect_and_decode_emoji_steganography(text):
    """
    Detects if a string contains hidden text using variation selectors and decodes it.
    
    Args:
        text (str): The input string, potentially containing an emoji with hidden text
        
    Returns:
        tuple: (bool, str) - (has_hidden_text, decoded_text)
            - has_hidden_text: True if hidden text was detected, False otherwise
            - decoded_text: The decoded hidden text, or empty string if none found
    """
    # Variation selectors ranges
    VARIATION_SELECTOR_START = 0xfe00
    VARIATION_SELECTOR_END = 0xfe0f
    VARIATION_SELECTOR_SUPPLEMENT_START = 0xe0100
    VARIATION_SELECTOR_SUPPLEMENT_END = 0xe01ef
    
    def from_variation_selector(code_point):
        if VARIATION_SELECTOR_START <= code_point <= VARIATION_SELECTOR_END:
            return code_point - VARIATION_SELECTOR_START
        elif VARIATION_SELECTOR_SUPPLEMENT_START <= code_point <= VARIATION_SELECTOR_SUPPLEMENT_END:
            return code_point - VARIATION_SELECTOR_SUPPLEMENT_START + 16
        else:
            return None
    
    # Convert string to list of code points
    code_points = [ord(c) for c in text]
    
    # Extract bytes from variation selectors
    decoded_bytes = []
    has_hidden_text = False
    
    for code_point in code_points:
        byte = from_variation_selector(code_point)
        if byte is not None:
            decoded_bytes.append(byte)
            has_hidden_text = True
    
    # If no variation selectors found, return False and empty string
    if not has_hidden_text:
        return False, ""
    
    # Convert bytes to text
    try:
        decoded_text = bytes(decoded_bytes).decode('utf-8')
        return True, decoded_text
    except UnicodeDecodeError:
        # If the bytes don't form valid UTF-8, it might not be intentional steganography
        return False, ""
    
if __name__ == "__main__":
    # Example usage
    test_strings = [
        "Hello world!",  # Regular text, no emoji
        "🙂",             # Just an emoji, no hidden text
        "🙂︀︁︂︃",        # Emoji with hidden text (assuming these variation selectors encode "test")
        "This is a normal message with a sneaky emoji 😎︀︁︂︃︄︅︆︇ at the end",
        "I bet an Amethyst user will get this first: 🎂󠅓󠅑󠅣󠅘󠅥󠄲󠅟󠄢󠄶󠅤󠅔󠅝󠅘󠄠󠅔󠄸󠄲󠅪󠄿󠅙󠄨󠅦󠅒󠅇󠅜󠅥󠅔󠄳󠄥󠅚󠅒󠄢󠅜󠅥󠅒󠄣󠄽󠅥󠅑󠅇󠄩󠅘󠅔󠅇󠄾󠅪󠅉󠅈󠅂󠅘󠅔󠄹󠄷󠅙󠅉󠅇󠅜󠄹󠄱󠄵󠄩󠄦󠄣󠅩󠅟󠄵󠄾󠅇󠅨󠅘󠅓󠄹󠄿󠅛󠅉󠅇󠄵󠄵󠅉󠅈󠄾󠄤󠅁󠄴󠅂󠅙󠄾󠅄󠅉󠄡󠄽󠅚󠅗󠄤󠄽󠄢󠅁󠅪󠄽󠄴󠄵󠄠󠅊󠄴󠅉󠅨󠅉󠅇󠄺󠅘󠅉󠅚󠄵󠅧󠄾󠅄󠅅󠅩󠅊󠄴󠄵󠄠󠅉󠅪󠅁󠅧󠅊󠅝󠅆󠅚󠅊󠅚󠅗󠄥󠄾󠅚󠅓󠅪󠄽󠅪󠅔󠅚󠅉󠄢󠅊󠅝󠄽󠄢󠅆󠅝󠅉󠅪󠄽󠄠󠅊󠄴󠄶󠅙󠄽󠄢󠅉󠅨󠄿󠄴󠄲󠅙󠄾󠅚󠄺󠅘󠅉󠄡󠅗󠅘󠄱󠄡󠅕󠅄󠄿󠄦󠅙󠅊󠄩󠅚󠅗󠅈󠅖󠅨󠅓󠅧󠄤󠄢󠅤󠅧󠅀󠅔󠅑󠅙󠅔󠅟󠅕󠅅󠄵󠅡󠄵󠄻󠅙󠅛󠅩󠄢󠄵󠅔󠅪󠅚󠅏󠄦󠅣󠅈󠅉󠅇󠅃󠅚󠅉󠅇󠅆󠅉󠄹󠄷󠅄󠅚󠅘󠅘󠄲󠄵󠄸󠄵󠄻󠅘󠅗󠄵󠅚󠄵󠄨󠄝󠅄󠅕󠄻󠅟󠄵󠅡󠅤󠅇󠅟󠅙󠄿󠅁󠅥󠄶󠄧󠄹󠅈󠄦󠅃󠅞󠅙󠄽󠅗󠅊󠅢󠄢󠅉󠅈󠄾󠅉󠄹󠄳󠅛󠄦󠅄󠅪󠅙󠅢󠅏󠄤󠅒󠅄󠅘󠄳󠅈󠅤󠅏󠅥󠅓󠄱󠅛󠅨󠅪󠅃󠄻󠅗󠅗󠅉󠅒󠄤󠄷󠄴󠅗󠄧󠅃󠅇󠅣󠄶󠄼󠄢󠅦󠅙󠄽󠅪󠅉󠅈󠄺󠅉󠄹󠄲󠅢󠅕󠅢󠅡󠅊󠅡󠅈󠄩󠅣󠄧󠄡󠄿󠅡󠄠󠅡󠅘󠅉󠄳󠅧󠄺󠄺󠅠󠅪󠅡󠅪󠄸󠄽󠅞󠄡󠄤󠄿󠅤󠅇󠅔󠅉󠅞󠄣󠄠󠄵󠅚󠅡󠄻󠅠󠄷󠄶󠅘󠄷󠄳󠄲󠅘󠅓󠄣󠅘󠄱󠄿󠅄󠅆󠅝󠅊󠄴󠄾󠅚󠅉󠅪󠄺󠅜󠅊󠅝󠅂󠅝󠄾󠅪󠄶󠅘󠄾󠅪󠅉󠄣󠄽󠅝󠄽󠅧󠄽󠅪󠅉󠄠󠄽󠅄󠄹󠄥󠅉󠅪󠅛󠄤󠅉󠅝󠄾󠅘󠅊󠅄󠄽󠅧󠅊󠅄󠅘󠅙󠄽󠄴󠅘󠅝󠅉󠄢󠅂󠅚󠄽󠄴󠅅󠅨󠅊󠅚󠄹󠄥󠅉󠄢󠅂󠅜󠅉󠅄󠅘󠅛󠄾󠅇󠄺󠅛󠄽󠄴󠅗󠄣󠅊󠄷󠄶󠅚󠅇󠄳󠄵󠄴󠄽󠄩󠄧󠅙󠄨󠅔󠄶󠅨󠅧󠅑󠄴󠄧󠅆󠄳󠅈󠅀󠅥󠅑󠄤󠅙󠄧󠅓󠄻󠅁󠅟󠅨󠄧󠅚󠅁󠅩󠅤󠅅󠅔󠅝󠅧󠅃󠄳󠅠󠅦󠄼󠅉󠄷󠄶󠅘󠅊󠄻󠄾󠅘󠅊󠅆󠅗󠅗󠅣󠅟󠅣󠅥󠅖󠅒󠅒󠄳󠄣󠅀󠄲󠅪󠄵󠄩󠄴󠄩󠄲󠅪󠅄󠅞󠅉󠅛󠅇󠅪󠄝󠅊󠄡󠅊󠄽󠄲󠅛󠄷󠅟󠅁󠅔󠅅󠅃󠅝󠅜󠅜󠅁󠄱󠄡󠅘󠅓󠄡󠅗󠅗󠄲󠅔󠅆󠄹󠄴󠄻󠄤󠄱󠄺󠅀󠄱󠅄󠅧󠅀󠄡󠄷󠄸󠄽󠄴󠄨󠅠󠅒󠄱󠅊󠅤󠅅󠄢󠅓󠅩󠅕󠅜󠅪󠅞󠄼󠄢󠄿󠄿󠅃󠄤󠅁󠄱󠄢󠄲󠅘󠅓󠅜󠅗󠅗󠅇󠄱󠄧󠅟󠅕󠅟󠅉󠄻󠅞󠅅󠄧󠅇󠅁󠅇󠅃󠅪󠅆󠅔󠅀󠅘󠅟󠅊󠅚󠅘󠅃󠅖󠅑󠅉󠅑󠅀󠅛󠅓󠄨󠅠󠄷󠄲󠄧󠅩󠅔󠅈󠅪󠄝󠄳󠅛󠅉󠅇󠄵󠅉󠅁󠄷󠄶󠅪󠅕󠄵󠄲󠅝󠄽󠅇󠄶󠅘󠅉󠅝󠄵󠅩󠄾󠄷󠅉󠅩󠅉󠅇󠅆󠅘󠄿󠅇󠄶󠅝󠄽󠅪󠅗󠅪󠄿󠅄󠄶󠅘󠄿󠅄󠄺󠅝󠅊󠄷󠅅󠅩󠅉󠅇󠅉󠄢󠅊󠅄󠄲󠅘󠄾󠄷󠄽󠄤󠄽󠄢󠅉󠄤󠄽󠅝󠄺󠅘󠅊󠄴󠅘󠅜󠅉󠅪󠄵󠄥󠄿󠅄󠅓󠅧󠅊󠄴󠄺󠅙󠅊󠄴󠄾󠅘󠄽󠅚󠅉󠅩󠄽󠅚󠄲󠅝󠅉󠅇󠄾󠅉󠄹󠅁󠄻󠅥󠅩󠄹󠄤󠅊󠄣󠄺󠄥󠅙󠅏󠄱󠄠󠅚󠅘󠄩󠅚󠅇󠅙󠄥󠅄󠅦󠅜󠄴󠅈󠄲󠄡󠅇󠅓󠅒󠅢󠄩󠅁󠅘󠅞󠅓󠄸󠄸󠅊󠅝󠅟󠅨󠄹󠅝󠄶󠅛󠅟󠄢󠄶󠅜󠅇󠄳󠄳󠅀󠅧󠅃󠅥󠄴󠅚󠅒󠅙󠅊󠄽󠄡󠄠󠄤󠅊󠄸󠄻󠅇󠄾󠄤󠅀󠄿󠅄󠄱󠅃󠅟󠅗󠄽󠅛󠄻󠄳󠄻󠅠󠅓󠅟󠄿󠅄󠅇󠄴󠅤󠅛󠅀󠅕󠄢󠄶󠅪󠅇󠄳󠄳󠄲󠅅󠅏󠄣󠄤󠄼󠅏󠅙󠄼󠄸󠅜󠅛󠅤󠄦󠄝󠄣󠅠󠅠󠅆󠅟󠄱󠄡󠄲󠅡󠅤󠅠󠅞󠅁󠅢󠄴󠄱󠅠󠅔󠅏󠄝󠅘󠅗󠅊󠄨󠅟󠄵󠅈󠄷󠄶󠅩󠅇󠄳󠄲󠅤󠅡󠄶󠅝󠄼󠅜󠅉󠅏󠄦󠅇󠅊󠄣󠅥󠅪󠅓󠄣󠄹󠅉󠅂󠄳󠅡󠅔󠄻󠄦󠅕󠅩󠅀󠅅󠅡󠄦󠅢󠄳󠅠󠅁󠄳󠅑󠄽󠅢󠅝󠅪󠄷󠅟󠅧"
    ]

    for s in test_strings:
        has_hidden, decoded = detect_and_decode_emoji_steganography(s)
        if has_hidden:
            print(f"Hidden text found: '{decoded}'")
        else:
            print(f"No hidden text in: '{s}'")