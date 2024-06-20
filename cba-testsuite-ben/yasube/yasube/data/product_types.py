import re

PRODUCT_TYPES_PATTERN = re.compile('(.+?\[)(?P<pattern>[^\]]+)')

# This is the list of product types arranged by satellite name and level.
# They can be used inside queries to randomly pick one with the
# following placeholder:
# {{ PRODUCT S1 L0 }}
# There are two subpatterns that can further expand a product type:
# - integer ranges: [1..6] > will be replaced by a random number between 1 and 6 included
# - choice: [X|Y|Z] > will be replaced by one of the pipe separated value
PRODUCT_TYPES = {
    'S1': {
        'L0': [
            'S[1..6]_RAW__0[S|C|N|A]',
            'IW_RAW__0[S|C|N|A]',
            'EW_RAW__0[S|C|N|A]',
            'WV_RAW__0[S|C|N|A]',
            'RF_RAW__0S',
            'EN_RAW__0S',
            'N[1..6]_RAW__0S',
            'GP_RAW__0_',
            'HK_RAW__0_',
        ],
        'L1': [
            'S[1..6]_SLC__1[S|A]',
            'S[1..6]_GRD[F|H]_1[S|A]',
            'IW_SLC__1[S|A]',
            'IW_GRD[H|M]_1[S|A]',
            'EW_SLC__1[S|A]',
            'EW_GRD[H|M]_1[S|A]',
            'EW_RTC__1S',
            'WV_SLC__1[S|A]',
        ],
        'L2': [
            'S[1..6]_OCN__2[S|A]',
            'IW_OCN__2[S|A]',
            'EW_OCN__2[S|A]',
            'WV_OCN__2[S|A]',
        ],
        'AUX': [
            'AUX_[PREORB|POEORB|RESORB|WND|WAV|ICE]',
        ],
    },
    'S2': {
        'L0': [
            'MSI_L0__[DS|GR]',
            'PRD_HKTM__'
        ],
        'L1': [
            'MSI_L1[A|B]_[DS|GR]',
            'MSI_L1C_[DS|TL|TC]',
        ],
        'L2': [
            'MSI_L2A_[DS|TL|TC]'
        ],
        'AUX': [
            'AUX_[PREORB|POEORB|RESORB|WND|WAV|ICE]',
        ],
    },
    'S3': {
        'L0': [
            'DO_0_[DOP|NAV]___',
            'GN_0_GNS___',
            'MW_0_MWR___',
            'OL_0_CR[0|1]___',
            'OL_0_EFR___',
            'SL_0_SLT___',
            'SR_0_SRA___',
            'SR_0_CAL___',
            'TM_0_HKM[_|2]__',
            'TM_0_NAT___',
        ],
        'L1': [
            'MW_1_[CAL|MWR]___',
            'OL_1_[EFR|ERR|RAC|SPC]___',
            'SL_1_RBT___',
            'SR_1_[CAL|SRA]___',
            'SR_1_SRA_[A_|BS]',
            'SY_1_MISR__'
        ],
        'L2': [
            'OL_2_L[F|R]R___',
            'SL_2_[LST|FRP]___',
            'SR_2_LAN___',
            'SY_2_[SYN|V10|VG1|VGP|VGK|AOD]___',
        ],
        'AUX': [
            'AUX_[PREORB|POEORB|RESORB|WND|WAV|ICE]',
        ],
    },
}
