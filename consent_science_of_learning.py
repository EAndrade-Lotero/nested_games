from markupsafe import Markup
from psynet.consent import Consent
from psynet.utils import get_translator
from psynet.timeline import Module, join, conditional, CodeBlock
from psynet.page import InfoPage, UnsuccessfulEndPage, RejectedConsentPage
from psynet.modular_page import ModularPage, PushButtonControl

_ = get_translator()
_p = get_translator(context=True)


def make_sure_cents(number):
    number_strs = str(number).split('.')
    whole = number_strs[0]
    cents = number_strs[1]
    if len(cents) < 2:
        cents = f"{cents}0"
    return f"{whole}.{cents}"


class consent_cococo_science_of_learning(Module, Consent):
    consent_text_template = Markup(
        "".join(
            [
                f"<h2 style='margin-bottom:0.3rem;font-weight:600;font-size:2.15rem'>{_p('page_heading', 'We need your consent to proceed')}</h2>",
                "<hr style='border:none;border-top:2px solid #000;margin:0.8rem 0 1.3rem'/>",

                # Overview
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('overview_title', 'Overview')}</h3>"
                + _p(
                    "overview_body",
                    """
<div class='consent-section'>
  <p>Jacoby’s lab is inviting you to take part in a research study called “Designing Smart Environments to Support Group Learning and Creativity.”
   We’ll explain the study to you and are happy to answer any questions you have. The study is led by Nori Jacoby from the Psychology Department at
    Cornell University, and it is supported by a grant from the National Science Foundation. </p>
</div>
""",
                ),

                # Purpose
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('purpose_title', 'What the study is about')}</h3>"
                + _p(
                    "purpose_body",
                    """
<div class='consent-section'>
  <p>This study looks at what helps groups learn. We want to see how people decide things together, do tasks as a team, and come up with creative ideas
   collaboratively. You’ll play an online game where what you do affects—and is affected by—other players. We’ll watch how you work with them and how changing the game’s rules changes the group’s behavior.</p>
</div>
""",
                ),

                # Procedure
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('procedure_title', 'What we will ask you to do')}</h3>"
                + _p(
                    "procedure_body",
                    """
<div class='consent-section'>
  <p>First, you’ll sign an online consent form and answer a few simple questions about yourself. Next, you’ll complete a brief survey, experiment, or small computer game. While playing,
   you may chat with other players or their avatars, share information, and help set the game’s rules. Some sessions also include quick puzzles that test skills like language, perception, or math. </p>
</div>
""",
                ),

                # Risks
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('risks_title', 'Risks and discomforts')}</h3>"
                + _p(
                    "risks_body",
                    """
<div class='consent-section'>
  <p>These experiments are behavioral and involve minimal risk, with no risks beyond those associated with normal computer use.
   We will not present any triggering, profane, or controversial content. The experiments are unlikely to cause any emotional distress,
   such as sadness or anxiety; however, some participants may find them boring. We make every effort to ensure the experiments are as engaging as possible.</p>
</div>
""",
                ),

                # Benefits
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('benefits_title', 'Benefits')}</h3>"
                + _p(
                    "benefits_body",
                    """
<div class='consent-section'>
  <p>There are no direct benefits to participating in the experiment, aside from contributing to scientific knowledge.
   The information gathered from this study may help others now or in the future by improving the design of learning and
   social systems. By participating, you also help advance the overall understanding of collective action and cognition.</p>
</div>
""",
                ),

                # Incentives
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('incentives_title', 'Incentives for participation ')}</h3>"
                + _p(
                    "incentives_body",
                    """
<div class='consent-section'>
  <p>We will compensate you at a rate of approximately $10 per hour.  The estimated duration of the experiment is <strong>{DURATION_MINUTES}</strong>
  minutes, with an expected payment of <strong>{TOTAL_PAYMENT_USD}</strong> USD.  Compensation will be processed through the recruitment service
  (e.g., Prolific), and we will share your alphanumeric participant ID, completion status, session timing, and details of
  compensation and bonus payments with them. You may also be eligible for a performance-based bonus, which may depend on
  your accuracy or on how others perceive your responses. If bonus opportunities are available, you will be notified during the experiment.</p>
</div>
""",
                ),

                # Privacy
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('privacy_title', 'Privacy/Confidentiality/Data Security')}</h3>"
                + _p(
                    "privacy_body",
                    """
<div class='consent-section'>
  <p>During the study, we will only know you by a participant ID made of alpha numeric code. We do not collect your personal
   details—just this code from the recruitment service (e.g., Prolific). If you choose to type something that reveals who you are,
   such as your real name, that text could be stored and seen by others, but providing such information is never required.
   We may share the study data with other researchers or make it public to support open science, but we will keep it de-identified
   so no one can link the data back to you. We also protect all data with strong security measures, including secure servers,
   encryption, and restricted access. We will do our best to keep your participation in this research study confidential
   to the extent permitted by law; however, it is possible that other people may need to review the research records and
   may find out about your participation in this study. For example, the following people/groups may check and copy records about this research:
</p>

  <ul>
    <li>The Office for Human Research Protections in the U. S. Department of Health and Human Services</li>
    <li>The research study sponsor, National Science Foundation</li>
    <li>Cornell University’s Institutional Review Board (a committee that reviews and approves research studies) and the Office for Research Integrity and Assurance</li>
  </ul>

  <p>We anticipate that your participation in this survey presents no greater risk than everyday use of the Internet.</p>

  <p>Please note that the experiment being conducted with the help of a recruiter such as Prolific, Amazon Mechanical Turk,
  CINT or Qualtrics, a company not affiliated with Cornell and with its own privacy and security policies that you can find
  at its website.</p>

  <p>Please note that email communication is neither private nor secure. Though we are taking precautions to protect your privacy,
   you should be aware that information sent through e-mail could be read by a third party. </p>

   <p>Data may exist on backups and server logs beyond the timeframe of this research project. Your confidentiality will
   be kept to the degree permitted by the technology being used. We cannot guarantee against interception of data sent via the internet by third parties. </p>


</div>
""",
                ),

                # data-sharing
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('sharing_title', 'Sharing De-identified Data Collected in this Research')}</h3>"
                + _p(
                    "sharing_body",
                    """
<div class='consent-section'>
  <p>De-identified data from this study may be shared with the research community at large to advance science and health.
   We will remove or code any personal information that could identify you before files are shared with other researchers
   to ensure that, by current scientific standards and known methods, no one will be able to identify you from the information we share. </p>
</div>
""",
                ),

                # Voluntary
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('voluntary_title', 'Taking part is voluntary')}</h3>"
                + _p(
                    "voluntary_body",
                    """
<div class='consent-section'>
  <p>Participation is completely voluntary. You can choose to stop participating at any time by simply closing the experiment
   window and ending the session. Before you participate, you must meet the following conditions:</p>
  <ol>
    <li>You are over 18 years old.</li>
    <li>You are an English speaker.</li>
    <li>You meet the technical requirements, such as having a microphone and the correct browser version as specified in the advertisement.</li>
  </ol>
  <p>At the start of the session, we may check for compliance with these conditions. If you do not meet them, your session
   will be terminated; however, you will still be compensated at the same hourly rate for participating in this initial test.
   The length of each experiment may vary, but you will be compensated at the same hourly rate, proportional to the amount
   of work and/or session duration. If you choose to withdraw early, you may not receive compensation or receive partial compensation.
   Please provide your consent only if you agree with these terms.</p>
</div>
""",
                ),

                # Follow-up
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('followup_title', 'Follow-up studies')}</h3>"
                + _p(
                    "followup_body",
                    """
<div class='consent-section'>
  <p>We may contact you again to request your participation in a follow up study. As always, your participation will be
   voluntary and we will ask for your explicit consent to participate in any of the follow up studies.</p>
</div>
""",
                ),

                # Questions
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('questions_title', 'If you have questions')}</h3>"
                + _p(
                    "questions_body",
                    """
<div class='consent-section'>
  <p>The main researcher conducting this study is Nori Jacoby, an assistant professor in the Psychology Department at Cornell University.
    Please ask any questions you have now. If you have questions later, you may contact Nori at {EMAIL} or at {PHONE}.
    If you have any questions or concerns regarding your rights as a subject in this study,
    you may contact the <strong>{IRB}</strong> for Human Participants at {IRB_PHONE}
    or access their website at <a href="{IRB_URL}" target="_blank">{IRB_URL}</a>. You may also report your concerns or
    complaints anonymously through <strong>Ethicspoint</strong> online at <a href="{ETHICS_URL}" target="_blank">{ETHICS_URL}</a> or
    by calling toll-free at {ETHICS_PHONE}. Ethicspoint is an independent organization that serves as a liaison between
    the University and the person bringing the complaint so that anonymity can be ensured.</p>
</div>
""",
                ),

                # Statement
                f"<h3 style='font-size:1.05rem;font-weight:600;margin-top:1.5rem'>{_p('statement_title', 'Statement of Consent ')}</h3>"
                + _p(
                    "statement_body",
                    """
<div class='consent-section'>
  <p>I have read the above information, and have received answers to any questions I asked. I consent to take part in the study.
  By choosing to consent electronically I confirm my consent to this study.</p>
</div>
""",
                ),
            ]
        )
    )

    time_estimate = 60


    def __init__(self, DURATION, PAYMENT, **kwargs):
        if DURATION is None or PAYMENT is None:
            raise ValueError(
                "Both DURATION and PAYMENT must be provided when initializing "
                "consent_cococo_science_of_learning(). "
                "Example: consent_cococo_science_of_learning(DURATION=10, PAYMENT=3)"
            )

        consent_text = str(self.consent_text_template)
        consent_text = consent_text.replace("{DURATION_MINUTES}", str(DURATION))
        consent_text = consent_text.replace("{TOTAL_PAYMENT_USD}", make_sure_cents(PAYMENT))

        consent_text = consent_text.format(
            EMAIL="kj338@cornell.edu",
            IRB = "Institutional Review Board (IRB)",
            PHONE="+1-607-255-3834",
            IRB_PHONE="607-255-6182",
            IRB_URL="https://researchservices.cornell.edu/offices/IRB",
            ETHICS_URL="www.hotline.cornell.edu",
            ETHICS_PHONE="1-866-293-3077"
        )
        consent_text = Markup(consent_text)

        class ConsentPageWrapper(ModularPage, Consent):
            pass

        consent_page = ConsentPageWrapper(
            "consent_choice",
            consent_text,
            PushButtonControl(
                choices=["I consent", "I do not consent"],
                labels=[_p("consent_answer", "I consent"), _p("consent_answer", "I do not consent")],
                arrange_vertically=False,
                bot_response="I consent"
            ),
            time_estimate=self.time_estimate,
        )

        noconsentgiven = conditional(
            "no_consent_feedback",
            lambda participant: participant.answer == "I do not consent",
            InfoPage(
                Markup(
                    f"<div class='alert alert-danger' role='alert' style='font-weight:600'>"
                    + _p("consent_feedback",
                         "You did not provide consent. Please return the HIT now and do not continue further.")
                    + "</div>"
                ),
                time_estimate=2,
            ),
        )

        elts = join(
            consent_page,
            conditional(
                "science_of_learning_consent_conditional",
                lambda experiment, participant: participant.answer == "I do not consent",
                join(
                    # noconsentgiven,
                    RejectedConsentPage(failure_tags=["science_of_learning_consent_rejected"])
                ),
            ),

            CodeBlock(
                lambda participant:
                participant.var.set("science_of_learning_consent", participant.answer)
            ),
        )

        super().__init__(
            "consent_cococo_science_of_learning",
            elts,
            **kwargs,
        )



