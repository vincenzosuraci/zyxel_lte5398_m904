from zyxel import ZyXEL_LTE5398_M904_Crawler

# ----------------------------------------------------------------------------------------------------------------------
#
# MAIN
#
# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # ------------------------------------------------------------------------------------------------------------------
    # ZyXEL LTE5398 M904
    # ------------------------------------------------------------------------------------------------------------------

    ip_address = "192.168.0.1"
    content = 'Iwb47Odxd5B2pNHeWa7bR3M03R6/RPNFwjZ/8PqDtht6N7hlNIzm3GZbwi3MAkfeKKvyxUAstbfO50sjqCJ+6tt61TSLPwa5s3dAEY6PDMCHnyqpFW6IpwzyHqig65Vfw1CqYjrK4HUAgqtM4hqF9ZMgl35D6aYNsCGYSypptXQ='
    key = 'Cy8Xo9UL9L1cIpfZ7cHbP0+VvCkjm2C/ij66DEvZxvpG4v1xBaCIFCsN6wLcwXZMegySFIhGVMPl+KqXiIxEEDRbZrzuxxW83fJmHLHm8uQXvsV2UHm9ErDblxiM8UspGL7WY3FgJjAwNmcdgSlTo/b4SKtZfKIxYimwIna8eniyDZ2jbmrvBOLrGoNh3pohYju9UtJgUg3RNT2l67H+jsm/QhV/MTXTp03FhMjEgmjJ2ByyWy+KjmNqwbaWz9nKR4MZZdGSngXs4ad+pkJY8QdQ1ESKFOMtWdU2lzgqB1ZuXVhoXcLub+B5hZm4pSlzOYlEKM4L3WNfed6eBWcqzw=='
    iv = 'Es8+IC4u2QnhRX27bbdPReuo8s4i0wVJnDeCqjTULxQ='
    aes_key = '490qltHlIA0iXoYgsHKqhyyq931dgM2CU+WIRcf3X5M='

    zyxel = ZyXEL_LTE5398_M904_Crawler(params={
        "ip_address": ip_address,
        "content": content,
        "key": key,
        "iv": iv,
        "aes_key": aes_key,
        "dynamic": False
    })

    zyxel.update_cell_status_data()
    # zyxel.test_aes_rsa_encrypt()


