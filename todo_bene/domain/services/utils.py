def mask_email(email: str) -> str:
    """Masque l'email selon le pattern : p*******.***t@******.*r"""
    if "@" not in email:
        return "****"
    
    user_part, domain_part = email.split("@")

    # Traitement User
    user_segments = user_part.split(".")
    masked_user = []
    for i, s in enumerate(user_segments):
        if i == 0:
            masked_user.append(s[0] + "*" * 7)
        else:
            masked_user.append("*" * (len(s) - 1) + s[-1] if len(s) > 0 else "")
    
    # Traitement Domaine
    dom_segments = domain_part.split(".")
    masked_dom = []
    for i, s in enumerate(dom_segments):
        if i == len(dom_segments) - 1: # Extension finale (.fr -> *r)
            masked_dom.append("*" * (len(s) - 1) + s[-1] if len(s) > 0 else "")
        else: # Corps du domaine (google -> ******)
            masked_dom.append("*" * len(s))
            
    return f"{".".join(masked_user)}@{".".join(masked_dom)}"
