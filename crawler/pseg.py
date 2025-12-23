import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from typing import Dict

from crawler import Crawler

# Load environment variables from .env file
load_dotenv()


class PSEG(Crawler):

    def __init__(self, **kwargs):
        super().__init__()
        if kwargs.get("cookies"):
            self.cookies.update(kwargs.get("cookies"))
        if kwargs.get("headers"):
            self.headers.update(kwargs.get("headers"))

    def login(self, url: str, username: str, password: str):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            page.goto(url)

            # Get all cookies
            cookies = context.cookies()

            # Convert to requests format
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

            browser.close()
        """
        After login:
        - Find the following:
            - input[@name=__RequestVerificationToken] and get the value
            - input[@id=hndIsMultipleAccount] and get the value
            - input[@id=hdnChatUserAccountNoNJ] and get the value
            - input[@id=gtmAccountBPN] and get the value
        - Export the cookies

        """

    def get_bill(self):
        token = ""
        cookies = {
            'remember_selected_domain': 'NJPublic',
            'currentselectedlanguage': 'en',
            'ASP.NET_SessionId': 'vdyegkm1ohhdaldw3als1fpd',
            'shell#lang': 'en',
            '__RequestVerificationToken': token,
            '.AspNet.Cookies': 'S-ioCXEOqpn5eDxIUQkdqBi_xie0QHtethErWe8TvLv3uGkJktdc_9uzpY1KZKD6P46E7QonWCYgb5ERHhCRSsUIdIim0rPio31C_w0YQnFicuRqxYNcR4vZsx01cIssFDH7QPnflBfSVWOnBnGWfnG3maKCBT_mR1Cnjdw0IKrnjJKf6BVo28pEMPHEOKwB2iyIS85bMTwnust9dgxkzBXCvGkoJlXRgnnJdReCfYyfCHbIZwc-F-crta6iumplQkgQCF8JVCCHT4gs_-UIxFmA5TPV6GdnkLCXMLkyaPn4s9kOO65USrTOXSEAD3RtyJufSOpA4hBVmRvci702WhroQh1Nsx3rSN6m5Domr43RADOFmisvU27hmwZP4AKb4bLjY8CJA2m0I7t2kSzNoCRvo3-15j3Os1d6DN0fwpaCmwX_zInOQ1utgvnHqmDh1QoWQ-oWtzN7n8fDoNrWoFID490W0sDz2pKZc2dfV9xgFU5w12IqDNhjfOmpVEPvNdlWbKkGYVi7yKoS-hbzwEDk7-j4FA6BaFbRCw14S6Ws5Y2glsZZb9JSmtbuj8wP92AHazDn6ho01ioDxmHka7K6DkLxc1UiOgR3AhyRkFANVneg8bWItQ4aUIJG5vnhYna6Axp1aV-Z19XFRN-3PjuyB-2DExGwJNvOTFwx7RQ3mBEVgRFlu2hsI_L16k_WaiXPooNjgJcBT65s2euGb1_JjuNreOE-9dkrMF1_Ooont_x2E26w3BsUxEqnsgTvTPjZv-NyCcoaGyZQuBDiJ5rqign_SJGNWIi4Eh3wAxHYK5VhuTzo5G-HEe1l8GtYmRHSI5gmK7yTI8v5nHfeKbVrz559PrhJGCwjA5WfmDjyApvvMEZpsnOTQqkvcj-VBV9Hr6cvQNW4LDWqS-TE3IDHNRBmeFBFfOIDrXgM75itT47aLVWMyJ1Aza0Sy3koQX80pzWHg6xlKViEL4QInQ8rrvKqrDuetBIUSPrQwHVX8n2o977mqCK0CxcmIpNH4cO00x8Evs8nEWZIZisTtESaZIMexvyAyWWZJ800fvJfwJsAX0_X18NrnN0PJwId7jAqBA1BomGl3k27odAocTJs9032uq9RRI0Lr8K8u8hOF9Iu6uavHcgpCzF035j1y89aRy98Jlf0t8k-N-OSHrmGlydW9EIjuUO7sGYsNHr8ZpZjXOGHQxEvr_8FYWx0N6ZzphjUToFfLhLcIu2yGDvzrUwKOdNBn7e1JUupwqjzMJV2Y65BLng2RsGTqaG0jikDaEFWK5wZTZBT233gLrSj2BwOYP8IEu8j0JKNZLcgxNsqGztcuAZy0AXuliwXLeHpSxJNu3nmXinpWJ-vOnnWrmKpwN8jhWAbpsC4fl4_x4O5eRCZYDM9DsJuTZGHYM_ENcedwiMN2k-eZcXR5rGzW-QSERD4F_8MqyYcEfJY_WS2JcXHlEe3N6mmbA-tmUMqD9Sx6pNbMIV0wF407MDXq_cgb5QZRnPwXW09Ubaesm6koK5KVqIndzvqv964zXwlDdPX93eGYcL7t1aAzvmu3KCft-ZOsFfM8FNK5FbGeixrcDKZLGyF8BHsCF13CcQX6RuJUE9q8TiZ9r9585QwfIUrEbr-QLCrCbUYN4GuZrDn0f4F4vzclTG4nvzIOQylS2yteri2WhGbghJfinc7uCPT6nXac7DwfRd-XaCEEViZkd3QX-_s3rYWoZZACdSDR1L0Pt0q7BWHFlQdym4HXRTSFLYD_SD2sV1Q1R6J1RpIsST3kOaES_UjFuz1im6GZeb8s5BT2Z4DG_ZvbEHlu_yGIEfmjoUHltjp_J_W8fe_b-MWBUT8XODFe_C8vHfAjUVnAyyYSyhQsbDNZfFYSvciAmiQFvHBdbAFtrXzZiwsWfoRH2iA69VVOaIMg-CYusHgFa70fRygoOgDIBTWZDaRDAmcshJ8M2wPiScqChn7Grb_u_3zro-CMDUY_ASHbFZNolvPHkmA2EpNPPtcCqSdeUYNPfPTIUXPqWcximLGLi0Cmqeh-wi2sLHg-eFVoxeaGPCInrPOVLxdETKIVgaxGLF3V8974NVtHuvGRMgn7XwpsQIQ9RhrKCcp5TuwPKHLzYUxTxX7Si1TNMgN8AbAJSv_OBEoCPEtboQZ6XQ9Q8QyuVtZInDoCYR3BSEdkVQq3q5YEn6IYPlFktkp9p-TzMXR1GBsmucze4GWrhKkpJRzVAlg_hesuZsyQnLK9i9SA6NOcC14o3k7-mrahMAI5fseYYMAJfJc6V1u98e7RlGEdYbnRuHBUKjl91kOFHe6YPaOVtF6MAw59aVVPPGEoVPirBajfFKNKiGuUWV82vWdpaCLXFdn7izHzrW6Ee03tEoN90I1AK4_Y04T00mSXim_uYzsvKZihzFrmpMjdyZJ633fcID0p_g5lJZH6Y6VKkxM_Sn3kHL8n4HhDF7sj5vomgYt-iEvqoFcGACJknYwEF1l5NCSizcoJmavKUdUcsYfW6ufMGgwhYipSfNokQbzYVfUh_DvldvNk3QSJzgmGDNrBLrNd3yohA21IcFkkLbVGtWt8mmB_nLVXszbn6t2E3dkYuIKnfYvP7Vu7n1ibOALd9_2Yr8-esnFMCBmjwINWw7FveQVTNa8JxCWWrgoIwgVNeb2_EaYu-6ZUDs0p9N9votb9E3yTWb0uya8PX4SDO6KTZIKrW7Y8La6Pod9nHdipYSk9YLj5u75bzXlWkctSiE9cfVvX-7nhDy1Gy2IDCl-09seBuE4Wd0-gkIqKMEVEA8l5gzFWBdY-_8pSAFQSMNdXKwbFyc47GND_NTuH1YA5ZhCgk_qiqRS50Ny2bLn73dYuz-8GHTpxvwSNff8aJKkDEN77Y-2Ze4TpOUipnsYYfVteMFDYzWUYjWyrp-TFwPCilh-wnGsUt1i5EMGXlXad8Ls4yT-U9Wof7mUu7FESh7nWoLS0mLROsmTOhWpqBoiTqXqAOpASnpPYua3NbWk-qZz2AU2sP51kKL4rEsCCQwYrNX2Due7JyDaD51i6UACxJBLKeHu3kEDVmxrnl0gnFtshWkoVrdyIi3sjdQFQkS48L-NmeXFSf7-aqUDZqdNZJCmXtjtsPzWQysD0Ktjs9e-k-vT7jkVfT3zBTuvXikmHkhT4d9tGN9fPDuDeXg_ysrGb2ie1NbCH_4o4vw12zMwHQzVjVe2hrXym7Eif-5ugp6MsKt3M7nPqEVd8Ts3x-95q2KcWS-DxuhbkRAAoPHtLRjWNth0uE4TKx3YTNiRkDq6idIcvTITUyqzybkHVYxH3Ya0wkvGEGah1q_N9sQ0wAVEcFXib6htnoDh01vR2Myo8UreybpD2qh1wNyYZC0o8mL2Gflvpt00mMWxDOVA',
            'OAM_userName': 'aHVudGVyX2JldHo=',
            'ProfileHeader_BPNumber': '1006081175',
            'ProfileHeader_AccNumber': '7691000200',
            'ProfileHeader_IsMulti': 'True',
            'ProfileHeader_AmountDue': '0.00',
            'OAM_DisplayName': 'SFVOVEVSIEJFVFog',
            'OAM_userFirstName': 'SFVOVEVSIEJFVFog',
        }

        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://nj.myaccount.pseg.com',
            'priority': 'u=1, i',
            'referer': 'https://nj.myaccount.pseg.com/myaccountdashboard?SelectAccountPage=1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }

        params = {
            'SelectAccountPage': '1',
        }

        data = {
            '__RequestVerificationToken': token,
            'scController': 'Common',
            'scAction': 'GetMyProfileHeaderData',
            'inBPNumber': '1006081175', # also in cookie
            'inAccountNumber': '7691000200',    # also in cookie
            'inAmountDue': '0.00',  # also in cookie
            'inIsMulti': 'True',    # also in cookie
        }

        response = self.post(
            'https://nj.myaccount.pseg.com/myaccountdashboard',
            params=params,
            cookies=cookies,
            headers=headers,
            data=data,
        )
        # r = requests.post(
        #     'https://nj.myaccount.pseg.com/myaccountdashboard',
        #     params=params,
        #     cookies=cookies,
        #     headers=headers,
        #     data=data,
        # )

    def add_payment(self, payment_details: Dict):
        pass

    def pay_bill(self):
        cookies = {
            'remember_selected_domain': 'NJPublic',
            'currentselectedlanguage': 'en',
            'ASP.NET_SessionId': 'vdyegkm1ohhdaldw3als1fpd',
            'shell#lang': 'en',
            '__RequestVerificationToken': 'Get-from-browser', # 'vXd4k6ZmxMGNVewCv1puKP4sXTnMlJlbmGlD_tTdxc8mMBdXipot0jrZBYjzr0YzLZKtM4oJTwG_2ewTu8XY251ZAPsIGoGHNLsp0Z9fUyo1',
            '.AspNet.Cookies': '0EgBF-QKElvjumBoCg9U8qpRHPYQI_qLJO5J4Ur2WaBp1lhrRneOKw9Slf4DT76LU1Lwbvfdtmef2xZtjh4grYYkmhEvudy4uKZbZXV3teQl3XMdBXDQ4KJcUmSSEe0gIfDup3JmLk3Xb32BVI_qAVCxycqbSslY-b0xm9pdcvGdoYL1mTVYAKIVc31Yz29UDvFBujC2F3SekwXvF25syaUcl2C3S9v4RMzYymW6Y8GQV8rFvCrBQXI0IFn8uE0yWLsFHrHPf8m-ydDVwt4FlxdTs64n1F46A37fCYu6sBgiXxQG_1ukWO0Ar0oTloSUYM2jlxcYvPjS_zbW2Dm1jRMKGA4mqozX4tdt38ftMmnd5TB8H72iF9mOV0uqDsPmozYxE6LI23I2O95B4yGz_owjdXem9SXXV0AjgOxYsEwyCspji2K66w7oaMcdNqPsGOt4AoYr8M8TutnTxqWIwO0Tut2pm9XL0NZOU82ORSgLCP1LbtX6MUKollzphZPQE4hS6NxrZGVqix6A1BAqtbXPOmMRGQ_UQooZqJQpxOkrEPGzIMMHJHoqUuaN8cA1z1zldiMyxA9gm2iIQBclmPrAcaSr1penLQQMWI76UFeVFZkO83lBxnilJnBMsfjMXXmd6P7axgb30he9YU2ueyPyI1Dw7juBO_Pw25lhmeoCJjMCzj7W73mwTAsMToAEXHs6gL2fgfX4vpPHcoaQCM962EjrZZPs6FbUMHgyAdJ5PRrXyCqO1OlgX3xvhYwdUgm0QsLEzievguFaMOTWYNvN1abVU5ZcNr1vAUd_m7L4zGyO8oDMCegK3k_ogogv5I4TzhptTgZkp9UJYdnRrgblL4rDjh4yS0zS0Ohy8o-wiK9sjiyeaTatsv24CuhrsST7j1DzypqI9Xvvyb6nHwlXPZ-MU1om-XOw5Auv7q6nOOpIZ_yq9kL670zPNOSO92nox6bjesGFo_aRdAsS03JQZmFAYzPuzKItKXPw3PSW5iOP7fVuFUK3dGeMvWFKilD5yTYkGdnCWw18goylut-SR6CbGhcBBQQDAeataSQVebVcLXvFvxeUTVjDRruBa7ys62_OwIFYWGxSkBtx5QS0RRO41-AyCtD6TiH6F9S9XBAbH54gWCvDTOFku7HliIWL1z0zjju3BO2sttgh8FBrQ8f_n3YenVafh2kPFJiLP0nlHsFphJU27ewQXG_M2iUG9msSH5umxnCkkc4-pZ7Q-5Cwry6Ocjsy7XO03RzgbyEAnUsfk2IV17pSd04sYD8mp6SGYShOr0C1lMWzpecqEW3oIir508LEQ4GN3iWHeigddK6kC1xAWCSsKJufRBsWVKJeE0gqXuZzvWi1ItsF4KZTbFrrLfdImy4_7EClU0noD94NuI1tHc9t3dgTXJrAIKTdRgqZOGnzg1Wlo57m6FpRXRgBZHQMbldZIqt3xtaTxVm-3p04dHHbxoEEtCUO0qMEj5b9wrc87Ch8uYIITl4QvLLN-Wr3mWuffdv_VTqHBohVW9Tj-crv2xXRJDvl2QAUMhHx-9SvTzeFrZR698MKH0Jlts6Ymgjp2gX2PZWOTP94mT2MG_TS3aqVCCia6PHuwLQtusFO7DL8dyiY65T_PA7NeYutCJQLGN0iLK-TgHrPezeJDsGc9nmGt5POzp4ITlHo60f8yyX-O2lE8cYPlPim3jvFwpgppB-l8er-KLidw_dBUsvxdcc6gBrx77URt16PEMuTRaRc1-TKrVIoFoxorrEn4hDB00l76a8BmLLRheb6kG2G9Eyj3NwroiR8h_lQ4A5mgC6_OXLmuSYUgmP8Mffw7ZgSjhjL35NpNVf3AloOyOw7xMYpyCXoIo6N5z0JuiXXitd_rCiCPAv899wYgUaSI3ElqW4kTgiBD1twhLhmluGBrnC13ObqsY8wdQ48lSIIirpPJbV9wIZVJ8eyRKA3Ayr1qYOyYo3vCwvK_JCBNj6Ee32uQ7b9mnMCZVw5LwZ3zC-GMxpv-RG3726-wXiv-sxr2XEcvciUXnmGMqB3cxUEzg2HU-3zgYGt3VEVRFRJFn6Gaaz-_9qVLx92LDnUZXQwMZP6H0KVKb-S4lsPEq0T9kqLJa-loOtTDgC-IMPrW3E28dIYx_KqyOrwefA02Osy3RvzNT3U4PiwmyE3anA_kUhRoetOM5UEMu8t0jJfxy__wgViFcO5RXjMXreHOKN1ekRi8j81aTygNTUOT9uwGIDhbj7yCDpZVkG4Bwjltd16j_SQE0s5-vKoT4lHpOMUyUuUpWWcylGe2EOAgej0djYRFKLQUX7suLW3_3G11GKzJfsjdoZos8fckQzJ_f2mVbqbF-Q6in7u5MwatlhC6X5e_OwRdfCBGFcM56N1PgMLuCoFIzSZMCeH1a-FQJvtECn-sWYeMtSbrLGnBpU9zowBS8WK_5_KnjJQgJy9_sulAK4h6uek_0WSFdLzoKLitmDZxBe9iG-fSK0jg-teeR4-LlZu46L6XMUO9qsxg0P0AG7FfUUsfP1YpzGokOluYK12xKqcx1vNqpJvXd-5PRN6S2KrC5l1tdhWtPLbECZ26qfoe7Qb1sqlWzP0mBBPGCyuRvb4Y2Rcg-Zn1gfiZUO7A3EGBfZ-0f3333U4ULidpWnYfiuf_BxRN6FasTXHHLeNNMd7J2M8-mClo-jIrESsfd_Vl78lL7qjypUHdEbpWeZI3fE1KFeqZcv9WbkTkzksV3GbMheCtbfS3KkBCMK7iNZIhI8BL9s1qoQmiympuYdL5kyQ3_0fvwm9skKol2jtEZ18O8CTE4Kt5WstMbxYwTry7hS0tpcVXGgl0RNKaIFd1-IWu-4nJnXlspJ2OYldTBq8kpvqMo5msjb7bnM3yophnHBjTE-qLPbu49gxvggt8Y02NCm3nav9pOp0BXZK_7xlXRPPYokT2DqHylXE_qtV5c0LCQpCIgPAaMji01pUo8JDysDXcTsWqUHUfwF9gFD00sdBv8D6Rov753lcRbWZu7OLil29gXvXer-vobkZcKotHsGVUy1gYFN_g9fJWovHWahSzoL5yihTuzhU_CtenC6HFu5z3TNod13-hlLqp5xyom_ucK7J9fYpj2w9KYJqO9GWIPPnVoQIGoxtSAAJICfEPHhQejAAdkyNANJiVLL2KKM0JlcHN_KBxDR2jDDz070XFH2OKPBzUeNmpj9K6PPUvzTXwd3sY7vr9e2S4gcIi6jxHf9MEDTkF-_6gYsj7EyGrglzV18nzmmjKUP2daUW1ygDYpgRRJukyEXy_S_RbNpBESodLOsjzGrcG7i-yuVBdG7xqReF3y7ae__RVXShQ9rNvgpY0z4n9-OEX4oJcyw2soUHiX_gKsYYrrrr2aIPQk73Es7DjnTj',
            'OAM_userName': 'aHVudGVyX2JldHo=',
            'ProfileHeader_BPNumber': '1006081175',
            'ProfileHeader_AccNumber': '7691000200',
            'ProfileHeader_IsMulti': 'True',
            'ProfileHeader_AmountDue': '0.00',
            'OAM_DisplayName': 'SFVOVEVSIEJFVFog',
            'OAM_userFirstName': 'SFVOVEVSIEJFVFog',
        }

        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://nj.myaccount.pseg.com',
            'priority': 'u=1, i',
            'referer': 'https://nj.myaccount.pseg.com/myaccountdashboard?SelectAccountPage=1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        params = {
            'SelectAccountPage': '1',
        }

        data = {
            '__RequestVerificationToken': 'mwSAfDKJoC0HYQuu_N6vP-vJ9I0AAihCXSilze69Kc54Wbz1adqG2TBrYZ_GEoANScE4LDFa1H3w4_j_SVs8owFDfYXZhBNr8JRULQ27C2thCPHqLx-loQFoGilms2HiczZqOkj1Z3RrUQrPKtid3Q2',
            'scController': 'PayBill',
            'scAction': 'PayMyBillEvent',
            'tabName': 'Make a Payment',
        }

        response = self.post(
            'https://nj.myaccount.pseg.com/myaccountdashboard',
            params=params,
            cookies=cookies,
            headers=headers,
            data=data,
        )


if __name__ == "__main__":
    pseg = PSEG(cookies={
        'remember_selected_domain': 'NJPublic',
        'shell#lang': 'en',
        'currentselectedlanguage': 'en',
        'OAM_userName': 'aHVudGVyX2JldHo=',
        'ProfileHeader_BPNumber': '1006081175',
        'ProfileHeader_AccNumber': '7691000200',
        'ProfileHeader_IsMulti': 'True',
        'ProfileHeader_AmountDue': '0.00',
        'OAM_DisplayName': 'SFVOVEVSIEJFVFog',
        'OAM_userFirstName': 'SFVOVEVSIEJFVFog'
    },
    headers={
        "X-Device-Fingerprint": "dhtTJBt0Iej5RQdV5Fjfg2sTZRD9csGN|a0f0a78c4a7fb8add3e3917464567094fb52b8ad629944559b53af1f7cf9a83f|d0af7df3216d87ca8a731cd4226186f2"
    })
    pseg.login(
        "https://nj.pseg.com/",
        username=os.getenv("PSEG_USER_NAME"),
        password=os.getenv("PSEG_PASSWORD"),
    )
