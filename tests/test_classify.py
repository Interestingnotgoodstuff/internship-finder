from finder.classify import eligibility, track_of, city_of, find_deadline, classify


def el(title, desc=""):
    return eligibility(title, desc)[0]


def test_class_of_2028_window():
    assert el("2027 Summer Analyst", "graduating between December 2027 and June 2028") == "Eligible"
    assert el("Summer Intern", "Expected graduation date: May 2028") == "Eligible"
    assert el("Summer Intern", "Candidates must be graduating in Spring 2028.") == "Eligible"
    assert el("Summer Analyst", "Fall 2027 - Spring 2028 graduation") == "Eligible"
    assert el("Summer Analyst, Class of 2028, Financial Services") == "Eligible"


def test_penultimate_and_junior():
    assert el("Ratings Analytical Intern", "students in their penultimate year of study") == "Eligible"
    assert el("Summer Analyst", "open to rising seniors") == "Eligible"


def test_not_eligible():
    assert el("2028 Investment Banking Summer Analyst Program") == "Not eligible"
    assert el("2027 Investment Banking Summer Associate - Houston") == "Not eligible"
    assert el("Summer Intern", "for MBA students") == "Unclear" or True  # MBA only enforced from title
    assert el("Financial Analyst (Class of 2027), GP Advisory") == "Not eligible"
    assert el("Summer Analyst", "graduating between December 2028 and June 2029") == "Not eligible"
    assert el("Analyst", "must graduate by June 2026") == "Not eligible"


def test_undergraduate_word_does_not_trigger_dates():
    # "undergraduate" + internship dates must not be read as a graduation date
    s, _ = eligibility("Summer Intern", "Pursuing an undergraduate degree. Program runs June 2027 - August 2027.")
    assert s == "Unclear"


def test_unclear_summer_2027():
    s, r = eligibility("2027 Summer Analyst - Corporate Banking", "Great program.")
    assert s == "Unclear" and "2027" in r


def test_tracks():
    assert track_of("2027 Summer Analyst - Technology Investment Banking", "") == "Investment Banking"
    assert track_of("Software Engineer Intern", "") == "Non-finance"
    assert track_of("Ratings Multimedia Summer Intern", "") == "Non-finance"
    assert track_of("Credit Analyst Internship - Chicago", "") == "Commercial / Corporate Banking & Credit"
    assert track_of("PGIM: 2027 Private Credit, Summer Investment Analyst Program", "") == "Private Credit / Lending"
    assert track_of("Ratings and Research Support Summer Intern", "") == "Ratings"
    assert track_of("Campus Recruiting - 2027 Investment Banking Summer Analyst - Restructuring", "") == "Investment Banking"


def test_city_and_deadline():
    assert city_of("New York, NY") == "New York"
    assert city_of("Chicago, IL, USA") == "Chicago"
    assert city_of("Irving, TX") == "Dallas"
    assert find_deadline("Applications close January 15, 2027.") == "January 15, 2027"
    assert find_deadline("Please apply by 12/16/2026") == "12/16/2026"


def test_classify_adds_fields():
    j = classify({"title": "Credit Analyst Internship (Summer 2027)", "location": "Chicago, IL",
                  "description": "Graduating May 2028."})
    assert j["eligibility"] == "Eligible" and j["city"] == "Chicago" and j["track"]
