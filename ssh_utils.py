import paramiko
import time
import os
import tempfile
import requests
import json
import re

# ---------- Конфигурация JAR ----------

def get_jar_url(server_type, version):
    if server_type == 'vanilla':
        vanilla_urls = {
            '26.2': 'https://piston-data.mojang.com/v1/objects/823e2250d24b3ddac457a60c92a6a941943fcd6a/server.jar',
            '26.1.2': 'https://piston-data.mojang.com/v1/objects/97ccd4c0ed3f81bbb7bfacddd1090b0c56f9bc51/server.jar',
            '26.1.1': 'https://piston-data.mojang.com/v1/objects/49c8195703ad0ba4f0a4efbccfd85a4a8ca57431/server.jar',
            '26.1': 'https://piston-data.mojang.com/v1/objects/3872a7f07a1a595e651aef8b058dfc2bb3772f46/server.jar',
            '1.21.11': 'https://piston-data.mojang.com/v1/objects/64bb6d763bed0a9f1d632ec347938594144943ed/server.jar',
            '1.21.10': 'https://piston-data.mojang.com/v1/objects/95495a7f485eedd84ce928cef5e223b757d2f764/server.jar',
            '1.21.9': 'https://piston-data.mojang.com/v1/objects/11e54c2081420a4d49db3007e66c80a22579ff2a/server.jar',
            '1.21.8': 'https://piston-data.mojang.com/v1/objects/6bce4ef400e4efaa63a13d5e6f6b500be969ef81/server.jar',
            '1.21.7': 'https://piston-data.mojang.com/v1/objects/05e4b48fbc01f0385adb74bcff9751d34552486c/server.jar',
            '1.21.6': 'https://piston-data.mojang.com/v1/objects/6e64dcabba3c01a7271b4fa6bd898483b794c59b/server.jar',
            '1.21.5': 'https://piston-data.mojang.com/v1/objects/e6ec2f64e6080b9b5d9b471b291c33cc7f509733/server.jar',
            '1.21.4': 'https://piston-data.mojang.com/v1/objects/4707d00eb834b446575d89a61a11b5d548d8c001/server.jar',
            '1.21.3':'https://piston-data.mojang.com/v1/objects/45810d238246d90e811d896f87b14695b7fb6839/server.jar',
            '1.21.2':'https://piston-data.mojang.com/v1/objects/7bf95409b0d9b5388bfea3704ec92012d273c14c/server.jar',
            '1.21.1':'https://piston-data.mojang.com/v1/objects/59353fb40c36d304f2035d51e7d6e6baa98dc05c/server.jar',
            '1.21':'https://piston-data.mojang.com/v1/objects/450698d1863ab5180c25d7c804ef0fe6369dd1ba/server.jar',
            '1.20.6':'https://piston-data.mojang.com/v1/objects/145ff0858209bcfc164859ba735d4199aafa1eea/server.jar',
            '1.20.5':'https://piston-data.mojang.com/v1/objects/79493072f65e17243fd36a699c9a96b4381feb91/server.jar',
            '1.20.4':'https://piston-data.mojang.com/v1/objects/8dd1a28015f51b1803213892b50b7b4fc76e594d/server.jar',
            '1.20.3':'https://piston-data.mojang.com/v1/objects/4fb536bfd4a83d61cdbaf684b8d311e66e7d4c49/server.jar',
            '1.20.2':'https://piston-data.mojang.com/v1/objects/5b868151bd02b41319f54c8d4061b8cae84e665c/server.jar',
            '1.20.1':'https://piston-data.mojang.com/v1/objects/84194a2f286ef7c14ed7ce0090dba59902951553/server.jar',
            '1.20':'https://piston-data.mojang.com/v1/objects/15c777e2cfe0556eef19aab534b186c0c6f277e1/server.jar',
            '1.19.4':'https://piston-data.mojang.com/v1/objects/8f3112a1049751cc472ec13e397eade5336ca7ae/server.jar',
            '1.19.3':'https://piston-data.mojang.com/v1/objects/c9df48efed58511cdd0213c56b9013a7b5c9ac1f/server.jar',
            '1.19.2':'https://piston-data.mojang.com/v1/objects/f69c284232d7c7580bd89a5a4931c3581eae1378/server.jar',
            '1.19.1':'https://piston-data.mojang.com/v1/objects/8399e1211e95faa421c1507b322dbeae86d604df/server.jar',
            '1.19':'https://piston-data.mojang.com/v1/objects/e00c4052dac1d59a1188b2aa9d5a87113aaf1122/server.jar',
            '1.18.2':'https://piston-data.mojang.com/v1/objects/c8f83c5655308435b3dcf03c06d9fe8740a77469/server.jar',
            '1.18.1':'https://piston-data.mojang.com/v1/objects/125e5adf40c659fd3bce3e66e67a16bb49ecc1b9/server.jar',
            '1.18':'https://piston-data.mojang.com/v1/objects/3cf24a8694aca6267883b17d934efacc5e44440d/server.jar',
            '1.17.1':'https://piston-data.mojang.com/v1/objects/a16d67e5807f57fc4e550299cf20226194497dc2/server.jar',
            '1.17':'https://piston-data.mojang.com/v1/objects/0a269b5f2c5b93b1712d0f5dc43b6182b9ab254e/server.jar',
            '1.16.5':'https://piston-data.mojang.com/v1/objects/1b557e7b033b583cd9f66746b7a9ab1ec1673ced/server.jar',
            '1.16.4':'https://piston-data.mojang.com/v1/objects/35139deedbd5182953cf1caa23835da59ca3d7cd/server.jar',
            '1.16.3':'https://piston-data.mojang.com/v1/objects/f02f4473dbf152c23d7d484952121db0b36698cb/server.jar',
            '1.16.2':'https://piston-data.mojang.com/v1/objects/c5f6fb23c3876461d46ec380421e42b289789530/server.jar',
            '1.16.1':'https://piston-data.mojang.com/v1/objects/a412fd69db1f81db3f511c1463fd304675244077/server.jar',
            '1.16':'https://piston-data.mojang.com/v1/objects/a0d03225615ba897619220e256a266cb33a44b6b/server.jar',
            '1.15.2':'https://piston-data.mojang.com/v1/objects/bb2b6b1aefcd70dfd1892149ac3a215f6c636b07/server.jar',
            '1.15.1':'https://piston-data.mojang.com/v1/objects/4d1826eebac84847c71a77f9349cc22afd0cf0a1/server.jar',
            '1.15':'https://piston-data.mojang.com/v1/objects/e9f105b3c5c7e85c7b445249a93362a22f62442d/server.jar',
            '1.14.4':'https://piston-data.mojang.com/v1/objects/3dc3d84a581f14691199cf6831b71ed1296a9fdf/server.jar',
            '1.14.3':'https://piston-data.mojang.com/v1/objects/d0d0fe2b1dc6ab4c65554cb734270872b72dadd6/server.jar',
            '1.14.2':'https://piston-data.mojang.com/v1/objects/808be3869e2ca6b62378f9f4b33c946621620019/server.jar',
            '1.14.1':'https://piston-data.mojang.com/v1/objects/ed76d597a44c5266be2a7fcd77a8270f1f0bc118/server.jar',
            '1.14':'https://piston-data.mojang.com/v1/objects/f1a0073671057f01aa843443fef34330281333ce/server.jar',
            '1.13.2':'https://piston-data.mojang.com/v1/objects/3737db93722a9e39eeada7c27e7aca28b144ffa7/server.jar',
            '1.13.1':'https://piston-data.mojang.com/v1/objects/fe123682e9cb30031eae351764f653500b7396c9/server.jar',
            '1.13':'https://piston-data.mojang.com/v1/objects/d0caafb8438ebd206f99930cfaecfa6c9a13dca0/server.jar',
            '1.12.2':'https://piston-data.mojang.com/v1/objects/886945bfb2b978778c3a0288fd7fab09d315b25f/server.jar',
            '1.12.1':'https://piston-data.mojang.com/v1/objects/561c7b2d54bae80cc06b05d950633a9ac95da816/server.jar',
            '1.12':'https://piston-data.mojang.com/v1/objects/8494e844e911ea0d63878f64da9dcc21f53a3463/server.jar',
            '1.11.2':'https://piston-data.mojang.com/v1/objects/f00c294a1576e03fddcac777c3cf4c7d404c4ba4/server.jar',
            '1.11.1':'https://piston-data.mojang.com/v1/objects/1f97bd101e508d7b52b3d6a7879223b000b5eba0/server.jar',
            '1.11':'https://piston-data.mojang.com/v1/objects/48820c84cb1ed502cb5b2fe23b8153d5e4fa61c0/server.jar',
            '1.10.2':'https://piston-data.mojang.com/v1/objects/3d501b23df53c548254f5e3f66492d178a48db63/server.jar',
            '1.10.1':'https://piston-data.mojang.com/v1/objects/cb4c6f9f51a845b09a8861cdbe0eea3ff6996dee/server.jar',
            '1.10':'https://piston-data.mojang.com/v1/objects/a96617ffdf5dabbb718ab11a9a68e50545fc5bee/server.jar',
            '1.9.4':'https://piston-data.mojang.com/v1/objects/edbb7b1758af33d365bf835eb9d13de005b1e274/server.jar',
            '1.9.3':'https://piston-data.mojang.com/v1/objects/8e897b6b6d784f745332644f4d104f7a6e737ccf/server.jar',
            '1.9.2':'https://piston-data.mojang.com/v1/objects/2b95cc7b136017e064c46d04a5825fe4cfa1be30/server.jar',
            '1.9.1':'https://piston-data.mojang.com/v1/objects/bf95d9118d9b4b827f524c878efd275125b56181/server.jar',
            '1.9':'https://piston-data.mojang.com/v1/objects/b4d449cf2918e0f3bd8aa18954b916a4d1880f0d/server.jar',
            '1.8.9':'https://launcher.mojang.com/v1/objects/b58b2ceb36e01bcd8dbf49c8fb66c55a9f0676cd/server.jar',
            '1.8.8':'https://launcher.mojang.com/v1/objects/5fafba3f58c40dc51b5c3ca72a98f62dfdae1db7/server.jar',
            '1.8.7':'https://launcher.mojang.com/v1/objects/35c59e16d1f3b751cd20b76b9b8a19045de363a9/server.jar',
            '1.8.6':'https://launcher.mojang.com/v1/objects/2bd44b53198f143fb278f8bec3a505dad0beacd2/server.jar',
            '1.8.5':'https://launcher.mojang.com/v1/objects/ea6dd23658b167dbc0877015d1072cac21ab6eee/server.jar',
            '1.8.4':'https://launcher.mojang.com/v1/objects/dd4b5eba1c79500390e0b0f45162fa70d38f8a3d/server.jar',
            '1.8.3':'https://launcher.mojang.com/v1/objects/163ba351cb86f6390450bb2a67fafeb92b6c0f2f/server.jar',
            '1.8.2':'https://launcher.mojang.com/v1/objects/a37bdd5210137354ed1bfe3dac0a5b77fe08fe2e/server.jar',
            '1.8.1':'https://launcher.mojang.com/v1/objects/68bfb524888f7c0ab939025e07e5de08843dac0f/server.jar',
            '1.8':'https://launcher.mojang.com/v1/objects/a028f00e678ee5c6aef0e29656dca091b5df11c7/server.jar',
            '1.7.10':'https://launcher.mojang.com/v1/objects/952438ac4e01b4d115c5fc38f891710c4941df29/server.jar',
        }

        return vanilla_urls.get(version, '')

    elif server_type == 'spigot':
        spigot_urls = {
            '26.1.2': 'https://getbukkit.org/get/PjkErgjMCMjr4gaPwAcYYV8oZ1XnvpK6',
            '26.1.1': 'https://getbukkit.org/get/asvGKHnuL3qFGqziNJBjwjmx4mEKdEzs',
            '26.1': 'https://getbukkit.org/get/fJA4ydcfvZokBYptPHNEQpwauUJcVpVn',
            '1.21.11': 'https://getbukkit.org/get/AfuyQcEkLcPU9p6jitBdBkGotQvy8ghM',
            '1.21.10': 'https://getbukkit.org/get/7Nsht2lVBEOXZbp9okiacncpLKvZFKi4',
            '1.21.8': 'https://getbukkit.org/get/8smOqbVnSl8RvSvlvkSNsUxEv0Y3g7Vo',
            '1.21.5': 'https://getbukkit.org/get/cNW08KHVlCEwof2IkXbxXIKeDPbfgMBU',
            '1.21.4': 'https://getbukkit.org/get/vUvveVKWgnYEO4zC7ey2pqkGtaAxvS6v',
            '1.21.3':'https://getbukkit.org/get/RnpgqIvNyXe7nFTZZJyIkXl4shuhFUXm',
            '1.21.1':'https://getbukkit.org/get/yqv2djplb2mijkqTIUUmC7F6pbJMpFdX',
            '1.20.6':'https://getbukkit.org/get/QRmEAkJCu1HcZkgxVSmVgHZYwZ03Ua1R',
            '1.20.4':'https://getbukkit.org/get/vdYtG2jRHgslyLJLaIUK2xVAL95LshGI',
            '1.20.2':'https://getbukkit.org/get/ZcRnnYaSJs89j5TUCLdyXVsmem6ovqnn',
            '1.20.1':'https://getbukkit.org/get/U9uE8nD9E8ubIns3NuTK6rnKrUVOVc45',
            '1.19.4':'https://getbukkit.org/get/XYtMHSKmmb8UNCj2RNwXmGjRvHISRwoj',
            '1.19.3':'https://getbukkit.org/get/h5zwRyDERLQVgY9ROBNlcyLLRzEsWSjH',
            '1.19.2':'https://getbukkit.org/get/OaTGj2mTbLKl9o6qGXn2wnCZBdwW3Yk6',
            '1.19.1':'https://getbukkit.org/get/SCPNVGrhmI4uSfXNOPi0N6AAvCtYTHgu',
            '1.19':'https://getbukkit.org/get/YH4OAZAZumfJ6EisLG4xfU9op3WvEEkc',
            '1.18.2':'https://getbukkit.org/get/M3CuBYuR72VaQB3W6T2TTbPiklfqSn1u',
            '1.18.1':'https://getbukkit.org/get/smdDWNBN1RV5KfOacaJvnDOlIf5BdAJN',
            '1.18':'https://getbukkit.org/get/DExv10cl86CUN62iB1Df4NVdG7GD1pNV',
            '1.16.5':'https://getbukkit.org/get/GSXo3m2tDdbXkJA5QAw0vLihBnEEP55G',
            '1.16.4':'https://getbukkit.org/get/iuObpmqGVCpBoU3BC823H5b2jKx3muCI',
            '1.16.3':'https://getbukkit.org/get/ZJZrBToD0A3qOwOG6FTaZ8j3ybrKe3oJ',
            '1.16.2':'https://getbukkit.org/get/WRBd7m29OQ4AmKDEOAU1C8ijgJrrAUio',
            '1.16.1':'https://getbukkit.org/get/1mFuDJYv8k9kpLvY4eyZ6bstqyXjHBdx',
            '1.15.2':'https://getbukkit.org/get/mpe1uTseEONyg3iFtJQaitrEoIFic75N',
            '1.15.1':'https://getbukkit.org/get/OT1jS2PYF5YnHuHbdjKBiPKBXGHzPThb',
            '1.15':'https://getbukkit.org/get/YeJiojZ6jVPQefdfxCT2ZzXXkHh3mmIn',
            '1.14.4':'https://getbukkit.org/get/rZlZWBTsIJauWb20uqHQTjIuv0ayKTMP',
            '1.14.3':'https://getbukkit.org/get/wKZI0DrixwfUBWAsiiyjqGLFpuKQ0uWo',
            '1.14.2':'https://getbukkit.org/get/npSdlqa7cDVGaQo62CjoqY4ZzqIJkKqz',
            '1.14.1':'https://getbukkit.org/get/h3hm8JHO3SlF0DP7RQMA4DwCm9mlK9l2',
            '1.14':'https://getbukkit.org/get/BT1o9lrMqDMj3hnXlRuHotimk7zX2F7g',
            '1.13.2':'https://getbukkit.org/get/jh3h8QSvol0gXPladGNin80nGid4DmWv',
            '1.13.1':'https://getbukkit.org/get/BxDmQtGsHUacEIUrXaJ5fy0m3Xp19A6i',
            '1.13':'https://getbukkit.org/get/pceKF1UGA4wPlu67X2lPMg4dfnhCjjb7',
            '1.12.2':'https://getbukkit.org/get/Uov36RPe0zZBdi42t7OwtMFq3qaCXNyT',
            '1.12.1':'https://getbukkit.org/get/OuENqxqgWDRSeS1Ec00KvnAjiLqRj57C',
            '1.12':'https://getbukkit.org/get/DWfRX0AnTBtgWJY7CbsLXcFJKj8HUCu7',
            '1.11.2':'https://getbukkit.org/get/a71XhriEGe5uvifgsghIIIZQKz549qtZ',
            '1.11':'https://getbukkit.org/get/g7znNa4ffhmOuMwZajenBNc2y5fFNYdi',
            '1.10.2':'https://getbukkit.org/get/emoWettOnCWTmPquJ86DpVh06tFEVCio',
            '1.9.4':'https://getbukkit.org/get/UZT6lu9xerOcWKTjKYdv3sIDVU2QGhf5',
            '1.9.2':'https://getbukkit.org/get/1VJgmwMfix4Qo2VJ7McbDo1ZekCPWMk6',
            '1.9':'https://getbukkit.org/get/aI5o1m9YfyNOu8yGzX9LvtYmXeWSfNZU',
            '1.8.8':'https://getbukkit.org/get/xo7CwyaiWNY7Ghtj3fR8bRCehoqLb5Pi',
            '1.8.3':'https://getbukkit.org/get/9rrkoYWkmC1MT0frDxNuAqYUogr9hfxR',
            '1.8':'https://getbukkit.org/get/J2wgWzOlirjx2drpuF4ncCxvVwqDR5p0'
        }

        return spigot_urls.get(version, '')

    elif server_type == 'paper':
        paper_urls = {
            '26.2':'https://fill-data.papermc.io/v1/objects/8600cc3b91ea38d7e836d562550b31d0fa3ed785d14dffc1a6d9dc1d36c21fa5/paper-26.2-56.jar',
            '26.1.2':'https://fill-data.papermc.io/v1/objects/1d70b1dab9cf4a6de615209a536f3a45a2186240253c428213ce2188ab95e5f7/paper-26.1.2-74.jar',
            '26.1.1':'https://fill-data.papermc.io/v1/objects/43d08ed52c7af4e9f72769122501a5c15f99c7ace0c428a3eef040fd3f6fdbc5/paper-26.1.1-29.jar',
            '1.21.11':'https://fill-data.papermc.io/v1/objects/5ffef465eeeb5f2a3c23a24419d97c51afd7dbb4923ff42df9a3f58bba1ccfba/paper-1.21.11-132.jar',
            '1.21.10':'https://fill-data.papermc.io/v1/objects/158703f75a26f842ea656b3dc6d75bf3d1ec176b97a2c36384d0b80b3871af53/paper-1.21.10-130.jar',
            '1.21.9':'https://fill-data.papermc.io/v1/objects/aec002e77c7566e49494fdf05430b96078ffd1d7430e652d4f338fef951e7a10/paper-1.21.9-59.jar',
            '1.21.8':'https://fill-data.papermc.io/v1/objects/8de7c52c3b02403503d16fac58003f1efef7dd7a0256786843927fa92ee57f1e/paper-1.21.8-60.jar',
            '1.21.7':'https://fill-data.papermc.io/v1/objects/83838188699cb2837e55b890fb1a1d39ad0710285ed633fbf9fc14e9f47ce078/paper-1.21.7-32.jar',
            '1.21.6':'https://fill-data.papermc.io/v1/objects/35e2dfa66b3491b9d2f0bb033679fa5aca1e1fdf097e7a06a80ce8afeda5c214/paper-1.21.6-48.jar',
            '1.21.5':'https://fill-data.papermc.io/v1/objects/2ae6ae22adf417699746e0f89fc2ef6cb6ee050a5f6608cee58f0535d60b509e/paper-1.21.5-114.jar',
            '1.21.4':'https://fill-data.papermc.io/v1/objects/5ee4f542f628a14c644410b08c94ea42e772ef4d29fe92973636b6813d4eaffc/paper-1.21.4-232.jar',
            '1.21.3':'https://fill-data.papermc.io/v1/objects/87e973e1d338e869e7fdbc4b8fadc1579d7bb0246a0e0cf6e5700ace6c8bc17e/paper-1.21.3-83.jar',
            '1.21.1':'https://fill-data.papermc.io/v1/objects/39bd8c00b9e18de91dcabd3cc3dcfa5328685a53b7187a2f63280c22e2d287b9/paper-1.21.1-133.jar',
            '1.21':'https://fill-data.papermc.io/v1/objects/ab9bb1afc3cea6978a0c03ce8448aa654fe8a9c4dddf341e7cbda1b0edaa73f5/paper-1.21-130.jar',
            '1.20.6':'https://fill-data.papermc.io/v1/objects/4b011f5adb5f6c72007686a223174fce82f31aeb4b34faf4652abc840b47e640/paper-1.20.6-151.jar',
            '1.20.5':'https://fill-data.papermc.io/v1/objects/3cd7da2f8df92e082a501a39c674aab3c0343edd179b86f5baccaebfc9974132/paper-1.20.5-22.jar',
            '1.20.4':'https://fill-data.papermc.io/v1/objects/cabed3ae77cf55deba7c7d8722bc9cfd5e991201c211665f9265616d9fe5c77b/paper-1.20.4-499.jar',
            '1.20.2':'https://fill-data.papermc.io/v1/objects/ba340a835ac40b8563aa7eda1cd6479a11a7623409c89a2c35cd9d7490ed17a7/paper-1.20.2-318.jar',
            '1.20.1':'https://fill-data.papermc.io/v1/objects/234a9b32098100c6fc116664d64e36ccdb58b5b649af0f80bcccb08b0255eaea/paper-1.20.1-196.jar',
            '1.20':'https://fill-data.papermc.io/v1/objects/1e4ccfc0599f491ee6fee4455d3722332ac5d78584fccd55cbb3b51e11504505/paper-1.20-17.jar',
            '1.19.4':'https://fill-data.papermc.io/v1/objects/e587d78cba3e99ef8c4bc24cf20cc3bdbbe89e33b0b572070446af4eb6be5ccf/paper-1.19.4-550.jar',
            '1.19.3':'https://fill-data.papermc.io/v1/objects/3007f2c638d5f04ed32b6adaa33053fe3634ccfa74345c83d3ea4982d38db5dc/paper-1.19.3-448.jar',
            '1.19.2':'https://fill-data.papermc.io/v1/objects/2eb5c7459ec94bcdc597ed711d549a3ab4b0fda13e412a0792a1a069b5903864/paper-1.19.2-307.jar',
            '1.19.1':'https://fill-data.papermc.io/v1/objects/5afe23a1fade92c547124fa874bc7d908fa676f49f09879fa876224b62e9d51b/paper-1.19.1-111.jar',
            '1.19':'https://fill-data.papermc.io/v1/objects/0d39cacc51a77b2b071e1ce862fcbf0b4a4bd668cc7e8b313598d84fa09fabac/paper-1.19-81.jar',
            '1.18.2':'https://fill-data.papermc.io/v1/objects/0578f18f4d632b494b468ec56b3b414b5b56fea087ee7d39cf6dcdf4c9d01f05/paper-1.18.2-388.jar',
            '1.18.1':'https://fill-data.papermc.io/v1/objects/a94917a4472c2cbc9907a15c666bbb784f95ecd7b53c77bc08fe71103e5487f5/paper-1.18.1-216.jar',
            '1.18':'https://fill-data.papermc.io/v1/objects/3c995f20dae4e4e21d5554fac957a0a8a5c85bd5bf34915fac4b4f16e0ef101b/paper-1.18-66.jar',
            '1.17.1':'https://fill-data.papermc.io/v1/objects/6cc1ee2f94253ce10b5374ed85fffc735a97d8f1b64db293683dfa24dd3cc05f/paper-1.17.1-411.jar',
            '1.17':'https://fill-data.papermc.io/v1/objects/760a93b94a58d619bd647d71af84688617d0444d22b716500bc6b343858dc871/paper-1.17-79.jar',
            '1.16.5':'https://fill-data.papermc.io/v1/objects/e67da4851d08cde378ab2b89be58849238c303351ed2482181a99c2c2b489276/paper-1.16.5-794.jar',
            '1.16.4':'https://fill-data.papermc.io/v1/objects/963268ed564ac7d2ec076463e921ffa09570235f587bbd1a4d91a23ca4264b66/paper-1.16.4-416.jar',
            '1.16.3':'https://fill-data.papermc.io/v1/objects/940303ee5f5bcc08377e388ea1c1daa109c1ac8c4d189dc67de1106853f2fc23/paper-1.16.3-253.jar',
            '1.16.2':'https://fill-data.papermc.io/v1/objects/e5e10517daaa9bd6d54a8a0d22d866e31da7c1b47cb9e425ffaac236fde75ec9/paper-1.16.2-189.jar',
            '1.16.1':'https://fill-data.papermc.io/v1/objects/929559ba1dfc6de2904e17289fb3d1ac95f0ab48c7540cf5b8c2f055fea9d59c/paper-1.16.1-138.jar',
            '1.15.2':'https://fill-data.papermc.io/v1/objects/bd2dd6f2cc489cf9e2bb800cb4fb6d63e9d293945d3ac10b09dd9c6098fa9f34/paper-1.15.2-393.jar',
            '1.15.1':'https://fill-data.papermc.io/v1/objects/22a7a19f378db8edf92cdba57d91ceea7e4fa6470b677e6bbe57e8f7e1d9a4dd/paper-1.15.1-62.jar',
            '1.15':'https://fill-data.papermc.io/v1/objects/8b726c0deb6c3a265d679a3d3a2c0f8e5243fbc6ddcfcaf42e24209cb1f829b4/paper-1.15-21.jar',
            '1.14.4':'https://fill-data.papermc.io/v1/objects/bd8ec5cdb22370d37816a6de26798df3d2b0d6f9c7c96c88ca45a1303fea50e8/paper-1.14.4-245.jar',
            '1.14.3':'https://fill-data.papermc.io/v1/objects/b6d2d8ac67d685141697a8cecd99c47baf604900007eb0e270fd6ea86cbbc540/paper-1.14.3-134.jar',
            '1.14.2':'https://fill-data.papermc.io/v1/objects/12034e578e014eb369e2929f3725bd409858bf94128e46d1f286d5be36c3cb0e/paper-1.14.2-107.jar',
            '1.14.1':'https://fill-data.papermc.io/v1/objects/2bcf8017485cc41b3e72daa7285a46f26a85d055b9d638bc9a07f77632168ad7/paper-1.14.1-50.jar',
            '1.14':'https://fill-data.papermc.io/v1/objects/338be77f5239c44cff3f80f5c107b5e61ac48fb39348bce7249303209201072a/paper-1.14-17.jar',
            '1.13.2':'https://fill-data.papermc.io/v1/objects/11e828d0565ab76a0a0e180c056364a95de44958cfd6a6af3f9b1dc70b03e9cd/paper-1.13.2-657.jar',
            '1.13.1':'https://fill-data.papermc.io/v1/objects/6637401d87d0f5db5aaee90d7103f52c5e1baaf6b6d4643a5793e7b02b5775cb/paper-1.13.1-386.jar',
            '1.13':'https://fill-data.papermc.io/v1/objects/00db82d214242c9345266d44ff8d11a8e857a1a02edf7cb5fcc2d1d973283129/paper-1.13-173.jar',
            '1.12.2':'https://fill-data.papermc.io/v1/objects/3a2041807f492dcdc34ebb324a287414946e3e05ec3df6fd03f5b5f7d9afc210/paper-1.12.2-1620.jar',
            '1.12.1':'https://fill-data.papermc.io/v1/objects/dba2219d674ad85e4ef2c41931d34b6fa4be75a887973ecaaf286727a03812da/paper-1.12.1-1204.jar',
            '1.12':'https://fill-data.papermc.io/v1/objects/1e7e88a2ed6f2b70fa3f6ec6611373458c5d72b2a8707e60921df601c791e60e/paper-1.12-1169.jar',
            '1.11.2':'https://fill-data.papermc.io/v1/objects/3d0f40ec1f9630dfdbafa626cc20c266d7fb90fc22583dc1b995e7fbfb76830d/paper-1.11.2-1106.jar',
            '1.10.2':'https://fill-data.papermc.io/v1/objects/83354d24a22b6265e76c089b3d17a568abb446c0ccd12c2452f5e148412b16c2/paper-1.10.2-918.jar',
            '1.9.4':'https://fill-data.papermc.io/v1/objects/15a5821ddeacc596432c3fbf24262a2d264f556060ecd6f1838fb01ab5629a81/paper-1.9.4-775.jar',
            '1.8.8':'https://fill-data.papermc.io/v1/objects/7ff6d2cec671ef0d95b3723b5c92890118fb882d73b7f8fa0a2cd31d97c55f86/paper-1.8.8-445.jar',
            '1.7.10':'https://fill-data.papermc.io/v1/objects/33772078d92e9dbb027602da016524ef29af5b4c12eaddac1fe2465b01108185/paper-1.7.10-2025.jar'
        }
        return paper_urls.get(version, '')

    elif server_type == 'purpur':
        purpur_urls = {
            '26.2':'https://api.purpurmc.org/v2/purpur/26.2/2607/download',
            '26.1.2':'https://api.purpurmc.org/v2/purpur/26.1.2/2592/download',
            '1.21.11':'https://api.purpurmc.org/v2/purpur/1.21.11/2568/download',
            '1.21.10':'https://api.purpurmc.org/v2/purpur/1.21.10/2535/download',
            '1.21.9':'https://api.purpurmc.org/v2/purpur/1.21.9/2505/download',
            '1.21.8':'https://api.purpurmc.org/v2/purpur/1.21.8/2497/download',
            '1.21.7':'https://api.purpurmc.org/v2/purpur/1.21.7/2477/download',
            '1.21.6':'https://api.purpurmc.org/v2/purpur/1.21.6/2465/download',
            '1.21.5':'https://api.purpurmc.org/v2/purpur/1.21.5/2450/download',
            '1.21.4':'https://api.purpurmc.org/v2/purpur/1.21.4/2416/download',
            '1.21.3':'https://api.purpurmc.org/v2/purpur/1.21.3/2358/download',
            '1.21.1':'https://api.purpurmc.org/v2/purpur/1.21.1/2329/download',
            '1.21':'https://api.purpurmc.org/v2/purpur/1.21/2284/download',
            '1.20.6':'https://api.purpurmc.org/v2/purpur/1.20.6/2233/download',
            '1.20.4':'https://api.purpurmc.org/v2/purpur/1.20.4/2176/download',
            '1.20.2':'https://api.purpurmc.org/v2/purpur/1.20.2/2095/download',
            '1.20.1':'https://api.purpurmc.org/v2/purpur/1.20.1/2062/download',
            '1.20':'https://api.purpurmc.org/v2/purpur/1.20/1990/download',
            '1.19.4':'https://api.purpurmc.org/v2/purpur/1.19.4/1985/download',
            '1.19.3':'https://api.purpurmc.org/v2/purpur/1.19.3/1933/download',
            '1.19.2':'https://api.purpurmc.org/v2/purpur/1.19.2/1858/download',
            '1.19.1':'https://api.purpurmc.org/v2/purpur/1.19.1/1751/download',
            '1.19':'https://api.purpurmc.org/v2/purpur/1.19/1735/download',
            '1.18.2':'https://api.purpurmc.org/v2/purpur/1.18.2/1632/download',
            '1.18.1':'https://api.purpurmc.org/v2/purpur/1.18.1/1566/download',
            '1.18':'https://api.purpurmc.org/v2/purpur/1.18/1433/download',
            '1.17.1':'https://api.purpurmc.org/v2/purpur/1.17.1/1428/download',
            '1.17':'https://api.purpurmc.org/v2/purpur/1.17/1255/download',
            '1.16.5':'https://api.purpurmc.org/v2/purpur/1.16.5/1171/download',
            '1.16.4':'https://api.purpurmc.org/v2/purpur/1.16.4/956/download',
            '1.16.3':'https://api.purpurmc.org/v2/purpur/1.16.3/808/download',
            '1.16.2':'https://api.purpurmc.org/v2/purpur/1.16.2/750/download',
            '1.16.1':'https://api.purpurmc.org/v2/purpur/1.16.1/710/download',
            '1.15.2':'https://api.purpurmc.org/v2/purpur/1.15.2/606/download',
            '1.15.1':'https://api.purpurmc.org/v2/purpur/1.15.1/397/download',
            '1.15':'https://api.purpurmc.org/v2/purpur/1.15/346/download',
            '1.14.4':'https://api.purpurmc.org/v2/purpur/1.14.4/337/download',
            '1.14.3':'https://api.purpurmc.org/v2/purpur/1.14.3/202/download',
            '1.14.2':'https://api.purpurmc.org/v2/purpur/1.14.2/126/download',
            '1.14.1':'https://api.purpurmc.org/v2/purpur/1.14.1/63/download',
        }
        return purpur_urls.get(version, '')

    elif server_type == 'foila':
        foila_urls = {
            '26.1.2': 'https://fill-data.papermc.io/v1/objects/607afd1c3320008e1ffd2eaee6780ace4419d5f8c527b75e79f259be79ebf57b/folia-26.1.2-8.jar',
            '1.21.11': 'https://fill-data.papermc.io/v1/objects/f52c408490a0225611e67907a3ca19f7e6da2c6bc899e715d5f46844e7103c39/folia-1.21.11-14.jar',
            '1.21.8': 'https://fill-data.papermc.io/v1/objects/233843cfd5001b6f658fcab549178d694cc37f0277d004ea295de0a94c57278f/folia-1.21.8-6.jar',
            '1.21.6': 'https://fill-data.papermc.io/v1/objects/917a8abaa542c1d0ef0e969693e227a7bfe1c42e671aaa806309e00a64efc234/folia-1.21.6-6.jar',
            '1.21.5': 'https://fill-data.papermc.io/v1/objects/ebeb8f2f9e97fd972c89ebc276bc547c6194c6542d3a1884e3cfef7228f69cdb/folia-1.21.5-12.jar',
            '1.21.4': 'https://fill-data.papermc.io/v1/objects/dcf2333211c1468c8eddc482bc8549600818cc661a709124a79c752f8fa2ac3a/folia-1.21.4-6.jar',
            '1.20.6': 'https://fill-data.papermc.io/v1/objects/a30625d8824b03aae64898b001b46bdc4424b0e5caee1a370af7b444d8ec361a/folia-1.20.6-6.jar',
            '1.20.4': 'https://fill-data.papermc.io/v1/objects/b0d55be3ba19cb6e040f0e7fba400e5224a271fbc7db73a9683aef7468425af9/folia-1.20.4-31.jar',
            '1.20.2': 'https://fill-data.papermc.io/v1/objects/d01746e0176b6ef1ae0bef65bc3fa44e2f2063eaa8ab78f9e941345268d4c9e5/folia-1.20.2-20.jar',
            '1.20.1': 'https://fill-data.papermc.io/v1/objects/c533d8886c60e1db17ebcf841b862731ab0a18d72377f37189930c3324eb7759/folia-1.20.1-17.jar',
            '1.19.4': 'https://fill-data.papermc.io/v1/objects/e6729be678110cf76b5feebaf4da09f447aacad907350f156bf163b561a9d979/folia-1.19.4-39.jar',
        }
        return foila_urls.get(version, '')

    elif server_type == 'bungee':
        bungee_urls = {
            'Lastest 1.7 - 1.20': 'https://ci.md-5.net/job/BungeeCord/lastSuccessfulBuild/artifact/bootstrap/target/BungeeCord.jar',
        }
        return bungee_urls.get(version, '')

    elif server_type == 'velocity':
        velocity_urls = {
            'Lastest': 'https://fill-data.papermc.io/v1/objects/a87eea534bd483209aa5ccb03822cb14d5006796d9c18a59e6e34cfd3c28b5b0/velocity-3.6.0-SNAPSHOT-613.jar',
        }
        return velocity_urls.get(version, '')

    elif server_type == 'mohist':
        mohist_urls = {
            '1.20.2': 'https://api.mohistmc.com/project/mohist/1.20.2/builds/174/download',
            '1.20.1': 'https://api.mohistmc.com/project/mohist/1.20.1/builds/471/download',
            '1.18.2': 'https://api.mohistmc.com/project/mohist/1.18.2/builds/411/download',
            '1.16.5': 'https://api.mohistmc.com/project/mohist/1.16.5/builds/362/download',
            '1.12.2': 'https://api.mohistmc.com/project/mohist/1.12.2/builds/389/download',
        }
        return mohist_urls.get(version, '')

# ---------- SSH и выполнение команд ----------
def ssh_connect(host, port, user, password):
    if not all([host, port, user, password]):
        raise ValueError("All arguments (host, port, user, password) are required")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            port=port,
            username=user,
            password=password,
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )
        transport = client.get_transport()
        if transport:
            transport.set_keepalive(30)
        return client
    except Exception as e:
        raise Exception(f"SSH connection failed: {str(e)}")

def execute_command(client, command, sudo=False, timeout=60, retries=3):
    if sudo:
        command = f"sudo {command}"
    for attempt in range(retries + 1):
        try:
            transport = client.get_transport()
            if not transport or not transport.is_active():
                raise Exception("SSH transport is not active")
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            stdout.close()
            stderr.close()
            stdin.close()
            return output, error, exit_status
        except Exception as e:
            try:
                stdout.close()
            except:
                pass
            try:
                stderr.close()
            except:
                pass
            try:
                stdin.close()
            except:
                pass
            if attempt < retries:
                time.sleep(5 * (attempt + 1))
                continue
            raise Exception(f"Command execution failed after {retries+1} attempts: {str(e)}")
    return "", "", -1

# ---------- Работа с Java ----------
def get_required_java_version(mc_version):
    base = re.sub(r'[-_].*$', '', mc_version)
    parts = base.split('.')
    if len(parts) >= 2:
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) >= 3 else 0
        if major == 1:
            if minor == 20 and patch >= 5:
                return 21
            elif minor >= 17:
                return 17
            else:
                return 8
        elif major >= 20:
            return 17
    return 17

def ensure_java_installed(client, password=None, required_version=None):
    if required_version is None:
        required_version = 17
    # Проверяем, какая Java установлена по умолчанию
    out, err, code = execute_command(client, "java -version 2>&1 | head -1 | grep -oE 'version \"[0-9]+' | grep -oE '[0-9]+'", timeout=5)
    if code == 0 and out.strip():
        installed = int(out.strip())
        if installed == required_version:
            # Проверяем путь
            find_path = f"update-alternatives --list java 2>/dev/null | grep 'java-{required_version}' | head -1"
            out_path, err_path, code_path = execute_command(client, find_path, timeout=5)
            if code_path == 0 and out_path.strip():
                return out_path.strip()
            else:
                for p in [f"/usr/lib/jvm/java-{required_version}-openjdk-amd64/bin/java", f"/usr/lib/jvm/java-{required_version}-openjdk/bin/java"]:
                    test_cmd = f"test -f {p} && echo '{p}'"
                    out_test, _, _ = execute_command(client, test_cmd, timeout=5)
                    if out_test.strip():
                        return out_test.strip()
                return "java"
    # Установка
    out_os, err_os, code_os = execute_command(client, "cat /etc/os-release | grep -E '^ID=' | cut -d= -f2")
    os_id = out_os.strip().lower().strip('"')
    pkg = f"openjdk-{required_version}-jre-headless"
    if 'ubuntu' in os_id or 'debian' in os_id:
        install_cmd = f"apt update && apt install -y {pkg}"
    elif 'centos' in os_id or 'rhel' in os_id or 'fedora' in os_id:
        if required_version == 8:
            pkg = "java-1.8.0-openjdk-headless"
        elif required_version == 11:
            pkg = "java-11-openjdk-headless"
        elif required_version == 17:
            pkg = "java-17-openjdk-headless"
        elif required_version == 21:
            pkg = "java-21-openjdk-headless"
        else:
            pkg = f"java-{required_version}-openjdk-headless"
        install_cmd = f"yum install -y {pkg} || dnf install -y {pkg}"
    else:
        raise Exception("Unsupported OS for auto Java installation")
    if password:
        escaped = password.replace("'", "'\\''")
        full_cmd = f"echo '{escaped}' | sudo -S bash -c '{install_cmd}'"
    else:
        full_cmd = f"sudo bash -c '{install_cmd}'"
    out, err, code = execute_command(client, full_cmd, timeout=120)
    if code != 0:
        raise Exception(f"Failed to install Java {required_version}: {err}")
    # Находим путь
    find_path = f"update-alternatives --list java 2>/dev/null | grep 'java-{required_version}' | head -1"
    out_path, err_path, code_path = execute_command(client, find_path, timeout=5)
    if code_path == 0 and out_path.strip():
        return out_path.strip()
    for p in [f"/usr/lib/jvm/java-{required_version}-openjdk-amd64/bin/java", f"/usr/lib/jvm/java-{required_version}-openjdk/bin/java"]:
        test_cmd = f"test -f {p} && echo '{p}'"
        out_test, _, _ = execute_command(client, test_cmd, timeout=5)
        if out_test.strip():
            return out_test.strip()
    return "java"

# ---------- Работа с портами ----------
def is_port_free(client, port):
    check_cmd = f"ss -tlnp | grep ':{port} ' || netstat -tlnp 2>/dev/null | grep ':{port} '"
    out, err, code = execute_command(client, check_cmd, timeout=5)
    return code != 0 or not out.strip()

def find_free_port(client, base_port=25565, max_attempts=20):
    for port in range(base_port, base_port + max_attempts):
        if is_port_free(client, port):
            return port
    raise Exception("No free port found")

# ---------- Работа с файлами ----------
def rename_jar_to_server(client, server_dir):
    check = f"test -f {server_dir}/server.jar"
    _, _, code = execute_command(client, check, timeout=5)
    if code == 0:
        return
    find_cmd = f"find {server_dir} -maxdepth 1 -name '*.jar' ! -name 'server.jar' | head -1"
    out, err, code = execute_command(client, find_cmd, timeout=5)
    if code == 0 and out.strip():
        mv_cmd = f"mv {out.strip()} {server_dir}/server.jar"
        execute_command(client, mv_cmd, timeout=5)

def get_file_content(client, server_name, file_path):
    """Читает содержимое файла в кодировке UTF-8."""
    full = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/{file_path}"
    # Команда cat выводит байты, мы их декодируем в UTF-8
    out, err, code = execute_command(client, f"cat {full}", timeout=5)
    if code == 0:
        try:
            return out
        except UnicodeDecodeError:
            # Если UTF-8 не подходит, пробуем другие кодировки (но лучше вернуть как есть)
            return out
    return None

def write_file_content(client, server_name, file_path, content):
    full = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/{file_path}"
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', delete=False, suffix='.tmp') as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        sftp = client.open_sftp()
        sftp.put(tmp_path, full)
        sftp.close()
    finally:
        os.remove(tmp_path)

def delete_file(client, server_name, file_path):
    full = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/{file_path}"
    execute_command(client, f"rm -rf {full}", timeout=10)

def create_directory(client, server_name, dir_path):
    full = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/{dir_path}"
    execute_command(client, f"mkdir -p {full}", timeout=10)

def list_files(client, server_name, path=''):
    full = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/{path}"
    out, err, code = execute_command(client, f"ls -la {full}", timeout=10)
    files = []
    if code == 0:
        lines = out.strip().split('\n')
        for line in lines:
            if not line or line.startswith('total'):
                continue
            parts = line.split(maxsplit=8)
            if len(parts) >= 9:
                name = parts[8]
                if name in ('.', '..'):
                    continue
                files.append({
                    'perms': parts[0],
                    'links': parts[1],
                    'user': parts[2],
                    'group': parts[3],
                    'size': parts[4],
                    'date': parts[5]+' '+parts[6]+' '+parts[7],
                    'name': name
                })
    return files

# ---------- Работа с server.properties ----------
def read_server_properties(client, server_name):
    content = get_file_content(client, server_name, 'server.properties')
    if not content:
        return {}
    props = {}
    for line in content.split('\n'):
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            props[k.strip()] = v.strip()
    return props

def write_server_properties(client, server_name, props):
    content = "\n".join([f"{k}={v}" for k, v in props.items()])
    write_file_content(client, server_name, 'server.properties', content)

# ---------- Screen-функции ----------
def ensure_screen_installed(client, password=None):
    out, err, code = execute_command(client, "which screen", timeout=5)
    if code == 0 and out.strip():
        return True
    out_os, err_os, code_os = execute_command(client, "cat /etc/os-release | grep -E '^ID=' | cut -d= -f2")
    os_id = out_os.strip().lower().strip('"')
    if 'ubuntu' in os_id or 'debian' in os_id:
        install_cmd = "apt update && apt install -y screen"
    elif 'centos' in os_id or 'rhel' in os_id or 'fedora' in os_id:
        install_cmd = "yum install -y screen || dnf install -y screen"
    else:
        raise Exception("Unsupported OS for screen installation")
    if password:
        escaped = password.replace("'", "'\\''")
        full_cmd = f"echo '{escaped}' | sudo -S bash -c '{install_cmd}'"
    else:
        full_cmd = f"sudo bash -c '{install_cmd}'"
    out, err, code = execute_command(client, full_cmd, timeout=60)
    if code != 0:
        raise Exception(f"Failed to install screen: {err}")
    return True

def is_server_running(client, server_name):
    # Проверка screen-сессии
    screen_cmd = f"screen -ls | grep 'mc-{server_name}'"
    out, err, code = execute_command(client, screen_cmd, timeout=5)
    if code == 0 and out.strip():
        return True
    # Проверка процесса Java
    username = client._transport.get_username()
    ps_cmd = f"ps aux | grep -v grep | grep 'java.*server.jar' | grep '/home/{username}/minecraft_servers/{server_name}' | wc -l"
    out2, err2, code2 = execute_command(client, ps_cmd, timeout=5)
    if code2 == 0 and int(out2.strip()) > 0:
        return True
    return False

def get_status(client, server_name):
    if is_server_running(client, server_name):
        return 'running'
    else:
        username = client._transport.get_username()
        cmd_dir = f"test -d /home/{username}/minecraft_servers/{server_name}"
        _, _, code_dir = execute_command(client, cmd_dir, timeout=5)
        if code_dir == 0:
            return 'stopped'
        else:
            return 'not_deployed'

def start_server_via_screen(client, server_name, password, java_path="java"):
    ensure_screen_installed(client, password)
    ensure_java_installed(client, password, get_required_java_version("1.20.4"))  # можно передавать версию
    username = client._transport.get_username()
    server_dir = f"/home/{username}/minecraft_servers/{server_name}"
    cmd = f"screen -dmS mc-{server_name} bash {server_dir}/start.sh"
    execute_command(client, cmd)

    if is_server_running(client, server_name):
        return True

    jar_check = f"test -f {server_dir}/server.jar"
    _, _, code = execute_command(client, jar_check, timeout=10)
    if code != 0:
        raise Exception("server.jar not found")

    # Удаляем session.lock (если есть)
    lock_file = f"{server_dir}/world/session.lock"
    execute_command(client, f"rm -f {lock_file}", timeout=5)

    # Запускаем через screen
    cmd = f"screen -dmS mc-{server_name} bash -c 'cd {server_dir} && {java_path} -Xmx1024M -Xms1024M -jar server.jar nogui'"
    out, err, code = execute_command(client, cmd, timeout=30)
    if code != 0:
        raise Exception(f"Screen start failed: {err}")

    # Проверяем, создалась ли сессия
    time.sleep(3)
    screen_check, _, _ = execute_command(client, f"screen -ls | grep 'mc-{server_name}'", timeout=5)
    if not screen_check.strip():
        # Fallback: попробуем через /usr/bin/screen
        fallback_cmd = f"/usr/bin/screen -dmS mc-{server_name} /bin/bash -c 'cd {server_dir} && {java_path} -Xmx1024M -Xms1024M -jar server.jar nogui'"
        out2, err2, code2 = execute_command(client, fallback_cmd, timeout=30)
        if code2 != 0:
            raise Exception(f"Fallback screen start failed: {err2}")
        time.sleep(3)
        screen_check2, _, _ = execute_command(client, f"screen -ls | grep 'mc-{server_name}'", timeout=5)
        if not screen_check2.strip():
            raise Exception("Screen session not created even with fallback")

    # Ждём готовности сервера
    if not wait_for_server(client, server_name, timeout=120):
        logs = get_logs(client, server_name, lines=30)
        raise Exception(f"Server not ready. Logs:\n{logs}")

    return True

def stop_server(client, server_name):
    # Отправляем stop через screen
    try:
        send_command(client, server_name, "stop")
        time.sleep(5)
    except:
        pass
    # Принудительно убиваем screen и процессы
    execute_command(client, f"screen -S mc-{server_name} -X quit", timeout=5)
    execute_command(client, f"pkill -f 'java.*{server_name}.*server.jar'", timeout=5)
    return True

def restart_server(client, server_name, password, server):
    stop_server(client, server_name)
    time.sleep(2)
    return start_server_via_screen(client, server.name, password, server.java_path if hasattr(server, 'java_path') else "java")

def delete_server(client, server_name):
    stop_server(client, server_name)
    execute_command(client, f"rm -rf ~/minecraft_servers/{server_name}", timeout=30)
    return True

def send_command(client, server_name, command):
    # Отправляем команду через screen
    cmd = f"screen -S mc-{server_name} -p 0 -X stuff '{command}\\015'"
    out, err, code = execute_command(client, cmd, timeout=10)
    if code != 0:
        raise Exception(f"Failed to send command: {err}")
    return True

def get_logs(client, server_name, lines=50):
    username = client._transport.get_username()
    server_dir = f"/home/{username}/minecraft_servers/{server_name}"
    log_path = f"{server_dir}/logs/latest.log"
    check = f"test -f {log_path}"
    _, _, code = execute_command(client, check, timeout=5)
    if code == 0:
        cmd = f"tail -n {lines} {log_path} 2>/dev/null"
    else:
        alt = f"{server_dir}/server.log"
        cmd = f"tail -n {lines} {alt} 2>/dev/null || echo 'Log file not found'"
    out, err, code = execute_command(client, cmd, timeout=10)
    return out

def wait_for_server(client, server_name, timeout=120):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_server_running(client, server_name):
            logs = get_logs(client, server_name, lines=3)
            if "Done" in logs:
                return True
        time.sleep(3)
    return False

def create_start_script(client, server_dir, java_path="java", ram="1024M"):
    script = f"""#!/bin/bash
cd {server_dir}
{java_path} -Xmx{ram} -Xms{ram} -jar server.jar nogui
"""
    with tempfile.NamedTemporaryFile(mode='w', newline='\n', delete=False, suffix='.sh') as tmp:
        tmp.write(script)
        tmp_path = tmp.name
    try:
        sftp = client.open_sftp()
        sftp.put(tmp_path, f"{server_dir}/start.sh")
        sftp.close()
    finally:
        os.remove(tmp_path)
    execute_command(client, f"chmod +x {server_dir}/start.sh")
    return True

# ---------- Бэкапы ----------
def create_backup(client, server_name):
    server_dir = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}"
    backup_dir = f"{server_dir}/backups"
    execute_command(client, f"mkdir -p {backup_dir}")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/backup_{timestamp}.zip"
    cmd = f"cd {server_dir} && zip -r {backup_file} . -x 'backups/*'"
    out, err, code = execute_command(client, cmd, timeout=60)
    if code == 0:
        return backup_file
    return None

def list_backups(client, server_name):
    server_dir = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/backups"
    out, err, code = execute_command(client, f"ls -la {server_dir}", timeout=5)
    backups = []
    if code == 0:
        lines = out.strip().split('\n')
        for line in lines:
            if not line or line.startswith('total'):
                continue
            parts = line.split(maxsplit=8)
            if len(parts) >= 9 and parts[8].endswith('.zip'):
                backups.append({
                    'name': parts[8],
                    'size': parts[4],
                    'date': parts[5]+' '+parts[6]+' '+parts[7]
                })
    return backups

def restore_backup(client, server_name, backup_name):
    server_dir = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}"
    backup_path = f"{server_dir}/backups/{backup_name}"
    stop_server(client, server_name)
    execute_command(client, f"find {server_dir} -mindepth 1 -maxdepth 1 ! -name 'backups' -exec rm -rf {{}} +", timeout=30)
    execute_command(client, f"unzip -o {backup_path} -d {server_dir}", timeout=30)
    # Удаляем session.lock
    execute_command(client, f"rm -f {server_dir}/world/session.lock", timeout=5)
    return True

def install_plugin(client, server_name, plugin_url, plugin_name):
    plugins_dir = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/plugins"
    execute_command(client, f"mkdir -p {plugins_dir}", timeout=10)
    cmd = f"wget -O {plugins_dir}/{plugin_name} {plugin_url}"
    execute_command(client, cmd, timeout=30)
    return True

# ---------- Modrinth установка ----------
def install_modrinth_project(client, server_name, project_id, version_id, project_type):
    if project_type not in ['mod', 'plugin']:
        raise ValueError("project_type must be 'mod' or 'plugin'")
    base_dir = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}"
    target_dir = f"{base_dir}/mods" if project_type == 'mod' else f"{base_dir}/plugins"
    execute_command(client, f"mkdir -p {target_dir}", timeout=10)

    url = f"https://api.modrinth.com/v2/version/{version_id}"
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f"Failed to get version info: {resp.text}")
    version_data = resp.json()
    files = version_data.get('files', [])
    if not files:
        raise Exception("No files found")
    file_info = files[0]
    download_url = file_info.get('url')
    filename = file_info.get('filename')
    if not download_url or not filename:
        raise Exception("Download URL or filename missing")
    cmd = f"curl -L -o {target_dir}/{filename} {download_url}"
    out, err, code = execute_command(client, cmd, timeout=60)
    if code != 0:
        raise Exception(f"Download failed: {err}\n{out}")
    return filename

# ---------- Развертывание сервера (deploy) ----------
def deploy_minecraft_server(client, server_name, server_type, mc_version, password):
    required_java = get_required_java_version(mc_version)
    java_path = ensure_java_installed(client, password, required_java)
    ensure_screen_installed(client, password)

    username = client._transport.get_username()
    base_dir = f"/home/{username}/minecraft_servers"
    server_dir = f"{base_dir}/{server_name}"
    execute_command(client, f"mkdir -p {server_dir}")

    jar_url = get_jar_url(server_type, mc_version)
    if not jar_url:
        raise Exception(f"No JAR URL found for {server_type} {mc_version}")

    cmd_download = f"curl -L -o {server_dir}/server.jar {jar_url}"
    out, err, code = execute_command(client, cmd_download, timeout=300)
    if code != 0:
        raise Exception(f"Download failed: {err}\n{out}")

    # Проверка JAR
    check_cmd = f"file {server_dir}/server.jar | grep -q 'Zip archive'"
    _, _, check_code = execute_command(client, check_cmd, timeout=5)
    if check_code != 0:
        head_cmd = f"head -c 200 {server_dir}/server.jar"
        head_out, _, _ = execute_command(client, head_cmd, timeout=5)
        raise Exception(f"Downloaded file is not a JAR (probably HTML). First 200 chars: {head_out}")

    rename_jar_to_server(client, server_dir)

    # eula.txt
    execute_command(client, f"echo 'eula=true' > {server_dir}/eula.txt")

    # server.properties (без RCON)
    properties_content = """#Minecraft server properties
enable-jmx-monitoring=false
rcon.port=25575
level-seed=
gamemode=survival
enable-command-block=false
enable-query=false
generator-settings=
enforce-secure-profile=true
level-name=world
motd=A Minecraft Server
query.port=25565
pvp=true
generate-structures=true
max-chained-neighbor-updates=1000000
difficulty=easy
network-compression-threshold=256
max-tick-time=60000
require-resource-pack=false
use-native-transport=true
max-players=20
online-mode=true
enable-status=true
allow-flight=false
initial-enabled-packs=vanilla
broadcast-rcon-to-ops=true
view-distance=10
server-ip=
resource-pack-prompt=
allow-nether=true
server-port=25565
enable-rcon=false
sync-chunk-writes=true
op-permission-level=4
prevent-proxy-connections=false
resource-pack=
hide-online-players=false
entity-broadcast-range-percentage=100
simulation-distance=10
rcon.password=
player-idle-timeout=0
debug=false
force-gamemode=false
rate-limit=0
hardcore=false
white-list=false
broadcast-console-to-ops=true
spawn-npcs=true
spawn-animals=true
snooper-enabled=false
function-permission-level=2
text-filtering-config=
spawn-monsters=true
enforce-whitelist=false
resource-pack-sha1=
spawn-protection=16
max-world-size=29999984
"""
    with tempfile.NamedTemporaryFile(mode='w', newline='\n', delete=False, suffix='.tmp') as tmp:
        tmp.write(properties_content)
        tmp_path = tmp.name
    try:
        sftp = client.open_sftp()
        sftp.put(tmp_path, f"{server_dir}/server.properties")
        sftp.close()
    finally:
        os.remove(tmp_path)

    # Проверяем порт
    props = read_server_properties(client, server_name)
    current_port = int(props.get('server-port', 25565))
    if not is_port_free(client, current_port):
        new_port = find_free_port(client, 25565)
        props['server-port'] = str(new_port)
        write_server_properties(client, server_name, props)

    # Запускаем через screen
    start_server_via_screen(client, server_name, password, java_path)

    return True

# ---------- Системная статистика ----------
def get_system_stats(client):
    stats = {'cpu_percent': 0.0, 'ram_total_mb': 0, 'ram_used_mb': 0, 'ram_percent': 0.0}
    try:
        out, err, code = execute_command(client, "mpstat 1 1 | tail -n1 | awk '{print 100 - $NF}'", timeout=3)
        if code == 0 and out.strip():
            cpu = float(out.strip())
        else:
            out2, err2, code2 = execute_command(client, "cat /proc/stat | grep '^cpu ' | awk '{print ($2+$4)*100/($2+$4+$5)}'", timeout=2)
            if code2 == 0 and out2.strip():
                cpu = float(out2.strip())
            else:
                cpu = 0.0
        stats['cpu_percent'] = round(cpu, 1)

        out_ram, err_ram, code_ram = execute_command(client, "free -m | grep Mem | awk '{print $2, $3}'", timeout=2)
        if code_ram == 0 and out_ram.strip():
            parts = out_ram.strip().split()
            if len(parts) >= 2:
                total = int(parts[0])
                used = int(parts[1])
                stats['ram_total_mb'] = total
                stats['ram_used_mb'] = used
                stats['ram_percent'] = round((used / total) * 100, 1) if total > 0 else 0.0
    except Exception:
        pass
    return stats

# ---------- Дополнительно: удаление мира ----------
def delete_world(client, server_name):
    username = client._transport.get_username()
    server_dir = f"/home/{username}/minecraft_servers/{server_name}"
    world_dir = f"{server_dir}/world"
    check_cmd = f"test -d {world_dir}"
    _, _, code = execute_command(client, check_cmd, timeout=5)
    if code == 0:
        execute_command(client, f"rm -rf {world_dir}", timeout=30)
        return True
    return False

def delete_plugins(client, server_name):
    username = client._transport.get_username()
    server_dir = f"/home/{username}/minecraft_servers/{server_name}"
    plugins_dir = f"{server_dir}/plugins"
    check_cmd = f"test -d {plugins_dir}"
    _, _, code = execute_command(client, check_cmd, timeout=5)
    if code == 0:
        execute_command(client, f"rm -rf {plugins_dir}", timeout=30)
        return True
    return False