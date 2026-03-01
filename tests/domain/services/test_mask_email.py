from todo_bene.domain.services.utils import mask_email

def test_mask_email_logic_strict():
    # p + 7* . *** + t @ ****** + . + * + r
    # Note : 'google' fait 6 chars, donc 6 étoiles.
    assert mask_email("philippe.test@google.fr") == "p*******.***t@******.*r"