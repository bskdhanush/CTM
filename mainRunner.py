
from CheckDeviceProvsion import check_Install_status

if __name__ == "__main__":
    option="1"
    option =f"{option},2,3,4"
    print(option)
    print(type(option))
    check_Install_status(option)

  #full_provisioning()