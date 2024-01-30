import pytest
import requests

from clean_links.unshorten import unshorten_url


# cassettes/{module_name}/test_single.yaml will be used
@pytest.mark.vcr
def test_unchanged():
    url = "https://example.com/"
    result = unshorten_url(url)
    assert result == {
        "url": url,
        "resolved": "https://example.com/",
        "status": 200,
        "exception": None,
    }


@pytest.mark.vcr
def test_single_redirect():
    url = "https://trib.al/5m7fAg3"
    result = unshorten_url(url)
    assert result == {
        "url": url,
        "resolved": "https://www.bloomberg.com/news/articles/2024-01-24/cryptocurrency-ai-electricity-demand-seen-doubling-in-three-years?cmpid%3D=socialflow-twitter-tech&utm_content=tech&utm_medium=social&utm_campaign=socialflow-organic&utm_source=twitter",
        "status": 200,
        "exception": None,
    }


@pytest.mark.vcr
def test_multiple_redirect():
    url = "https://hubs.la/Q01HRjhm0"
    result = unshorten_url(url)
    assert result == {
        "url": url,
        "resolved": "https://app.east.mentorspaces.com/#!/orgs/6aab4989-2bd1-7ec9-6e3f-56f3128815c8/?utm_content=242450506&utm_medium=social&utm_source=twitter&hss_channel=tw-18419094&_branch_match_id=1280732352261121106&utm_campaign=fall-recruiting&_branch_referrer=H4sIAAAAAAAAAx3KUQqEIBAA0Nv0V1rYsgXSUcJmB5R0FGek61f7%2B3hepPCqVEKSXLk4QB5cKUMMdCriA7cmaYdM8gw7mcnMetaf7tWEv9CS5QzBxb9wbhXQyhVEsHaeeQfviDA%2B1o9fMy56MTdcnGABdQAAAA%3D%3D",
        "status": 200,
        "exception": None,
    }


@pytest.mark.vcr
def test_expired_certificate_ignore():
    url = "https://expired.badssl.com/"
    result = unshorten_url(url, verify=False)
    assert result == {
        "url": url,
        "resolved": "https://expired.badssl.com/",
        "status": 200,
        "exception": None,
    }


@pytest.mark.vcr
def test_resolve_to_mailto():
    url = "https://tinyurl.com/NewwAlemAndKibrom"
    result = unshorten_url(url)
    assert result["url"] == url
    assert (
        result["resolved"]
        == "mailto:center@moi.gov.eg,%20ambassaden.kairo@gov.se,%20emb.cairo@mfa.no,%20info@kairo.diplo.de,%20Consulateofegypt@hotmail.com,%20consulate@egyptembassy.net,%20egyptnyc@gmail.com,%20embassy@egyptembassy.net,%20egypt.consulate@videotron.ca,%20Embassy.canberra@mfa.gov.eg,%20info@egyptianconsulate.org.au,%20embassy@egyptian-embassy.de,%20gen-kons-et-hh@gmx.de,%20emb.egypt@yahoo.gr,%20info@embegyptireland.ie,%20info@ambeg.nl,%20embassyofegypt@telia.com,%20consulate.london@mfa.gov.eg,%20info@egyptianconsulate.co.uk,%20eg.sec.be@hotmail.com,%20egyptembassy@embassyofegypt.be,%20embegypthelsinki.diplo@hotmail.com,%20secertaryofembassy@hotmail.com,%20Embassy.Helsinki@mfa.gov.eg,%20egyptembassyportugal@net.novis.pt,%20ufficioconsolegeneralegitto@gmail.com,%20consolatogenerale.egitto.milano@gmail.com,%20ambegitto@gmail.com,%20egyptianembassy@xtra.co.nz,%20consulategypte@orange.fr,%20embegypt.dk@gmail.com,%20areca@unhcr.org,%20arealpro@unhcr.org,%20consularcairoacs@state.gov,%20kitidi@unhcr.org,%20cheshirk@unhcr.org,%20beshay@unhcr.org,%20arecapi@unhcr.org?subject=URGENT%20CALL%20TO%20ACTION%3A%20Save%20Alem%20and%20Kibrom's%20lives&body=To%20Whom%20it%20May%20Concern%3A%0A%0AAlem%20Tesfay%20Abraham%20and%20Kibrom%20Adhanom%20Okbazghi%20are%20two%20Eritrean%20asylum-seekers%20who%20have%20been%20detained%20without%20charge%20in%20Egypt%20since%202012%20and%202014%2C%20respectively.%20They%20now%20are%20facing%20deportation%20to%20Eritrea%20without%20ever%20receiving%20the%20opportunity%20to%20register%20as%20refugees%20with%20UNHCR%20in%20Egypt.%20On%209%20September%2C%20they%20were%20taken%20from%20prison%20to%20a%20hospital%20in%20Cairo%20to%20take%20PCR%20tests%20and%20were%20informed%20by%20a%20prison%20official%20that%20they%20would%20be%20deported%20to%20Eritrea%20on%20the%20oncoming%20days.%0A%0AForcibly%20returning%20Alem%20and%20Kibrom%20to%20Eritrea%2C%20where%20they%20fled%20indefinite%20military%20conscription%20and%20where%20they%20would%20face%20persecution%2C%20is%20a%20grave%20breach%20of%20international%20law.%20Eritrean%20asylum-seekers%20who%20are%20forcibly%20returned%20to%20Eritrea%20risk%20arbitrary%20arrest%2C%20forced%20disappearance%20and%20indefinite%20detention%20without%20charges.%20As%20widely%20documented%20by%20many%20NGOs%20as%20well%20as%20the%20UN%20Human%20Rights%20Council%2C%20citizens%20in%20Eritrea%20are%20held%20in%20prisons%20incommunicado%2C%20in%20unsanitary%20living%20conditions%2C%20where%20torture%20and%20other%20ill%20treatments%20are%20taking%20place%20to%20present.%0A%0AForcing%20Alem%20and%20Kibrom%20back%20to%20the%20nation%20they%20are%20seeking%20asylum%20from%20violates%20the%201951%20Convention%20and%201967%20Protocol%2C%20two%20International%20Laws%20Egypt%20has%20agreed%20to.%20They%20deserve%20the%20right%20to%20be%20resettled%20by%20will%2C%20to%20a%20country%20willing%20to%20accept%20them.%20We%20urge%20you%2C%20the%20Egyptian%20authorities%2C%20and%20all%20other%20relevant%20bodies%2C%20to%20help%20stop%20the%20forced%20repatriation%20of%20Alem%20and%20Kibrom%20and%20protect%20them%20from%20persecution%20and%20grant%20them%20their%20long-awaited%20freedom.%20%0A%0A%23JusticeforAlemAndKibrom%0A%0ASincerely%2C"
    )
    assert result["status"] is None
    assert (
        result["exception"]
        == 'InvalidSchema: No connection adapters were found for "mailto:center@moi.gov.eg,%20ambassaden.kairo@gov.se,%20emb.cairo@mfa.no,%20info@kairo.diplo.de,%20Consulateofegypt@hotmail.com,%20consulate@egyptembassy.net,%20egyptnyc@gmail.com,%20embassy@egyptembassy.net,%20egypt.consulate@videotron.ca,%20Embassy.canberra@mfa.gov.eg,%20info@egyptianconsulate.org.au,%20embassy@egyptian-embassy.de,%20gen-kons-et-hh@gmx.de,%20emb.egypt@yahoo.gr,%20info@embegyptireland.ie,%20info@ambeg.nl,%20embassyofegypt@telia.com,%20consulate.london@mfa.gov.eg,%20info@egyptianconsulate.co.uk,%20eg.sec.be@hotmail.com,%20egyptembassy@embassyofegypt.be,%20embegypthelsinki.diplo@hotmail.com,%20secertaryofembassy@hotmail.com,%20Embassy.Helsinki@mfa.gov.eg,%20egyptembassyportugal@net.novis.pt,%20ufficioconsolegeneralegitto@gmail.com,%20consolatogenerale.egitto.milano@gmail.com,%20ambegitto@gmail.com,%20egyptianembassy@xtra.co.nz,%20consulategypte@orange.fr,%20embegypt.dk@gmail.com,%20areca@unhcr.org,%20arealpro@unhcr.org,%20consularcairoacs@state.gov,%20kitidi@unhcr.org,%20cheshirk@unhcr.org,%20beshay@unhcr.org,%20arecapi@unhcr.org?subject=URGENT%20CALL%20TO%20ACTION%3A%20Save%20Alem%20and%20Kibrom\'s%20lives&body=To%20Whom%20it%20May%20Concern%3A%0A%0AAlem%20Tesfay%20Abraham%20and%20Kibrom%20Adhanom%20Okbazghi%20are%20two%20Eritrean%20asylum-seekers%20who%20have%20been%20detained%20without%20charge%20in%20Egypt%20since%202012%20and%202014%2C%20respectively.%20They%20now%20are%20facing%20deportation%20to%20Eritrea%20without%20ever%20receiving%20the%20opportunity%20to%20register%20as%20refugees%20with%20UNHCR%20in%20Egypt.%20On%209%20September%2C%20they%20were%20taken%20from%20prison%20to%20a%20hospital%20in%20Cairo%20to%20take%20PCR%20tests%20and%20were%20informed%20by%20a%20prison%20official%20that%20they%20would%20be%20deported%20to%20Eritrea%20on%20the%20oncoming%20days.%0A%0AForcibly%20returning%20Alem%20and%20Kibrom%20to%20Eritrea%2C%20where%20they%20fled%20indefinite%20military%20conscription%20and%20where%20they%20would%20face%20persecution%2C%20is%20a%20grave%20breach%20of%20international%20law.%20Eritrean%20asylum-seekers%20who%20are%20forcibly%20returned%20to%20Eritrea%20risk%20arbitrary%20arrest%2C%20forced%20disappearance%20and%20indefinite%20detention%20without%20charges.%20As%20widely%20documented%20by%20many%20NGOs%20as%20well%20as%20the%20UN%20Human%20Rights%20Council%2C%20citizens%20in%20Eritrea%20are%20held%20in%20prisons%20incommunicado%2C%20in%20unsanitary%20living%20conditions%2C%20where%20torture%20and%20other%20ill%20treatments%20are%20taking%20place%20to%20present.%0A%0AForcing%20Alem%20and%20Kibrom%20back%20to%20the%20nation%20they%20are%20seeking%20asylum%20from%20violates%20the%201951%20Convention%20and%201967%20Protocol%2C%20two%20International%20Laws%20Egypt%20has%20agreed%20to.%20They%20deserve%20the%20right%20to%20be%20resettled%20by%20will%2C%20to%20a%20country%20willing%20to%20accept%20them.%20We%20urge%20you%2C%20the%20Egyptian%20authorities%2C%20and%20all%20other%20relevant%20bodies%2C%20to%20help%20stop%20the%20forced%20repatriation%20of%20Alem%20and%20Kibrom%20and%20protect%20them%20from%20persecution%20and%20grant%20them%20their%20long-awaited%20freedom.%20%0A%0A%23JusticeforAlemAndKibrom%0A%0ASincerely%2C"'
    )


def test_missing_schema():
    url = "I AM NOT AN URL"
    with pytest.raises(requests.exceptions.MissingSchema):
        unshorten_url(url)


# def test_expired_certificate_verify():
#     url = "https://expired.badssl.com/"
#     result = unshorten_url(url, verify=True)
#     assert result["url"] == "https://expired.badssl.com/"
#     assert result["resolved"] == "https://expired.badssl.com/"
#     assert result["status"] is None
#     assert result["exception"].startswith("SSLError:")
