import telnetlib
import time
########################## Barcode Reader (Cognex Cam) ##########################

host_cognex = '10.32.73.18'
 
################################ Commands ################################
 
beep = b'||>BEEP 3 2\r\n'
ethernet_ip_enabled = b'||>GET ETHERNET-IP.ENABLED\r\n'
trigger_type = b'||>GET TRIGGER.TYPE\r\n'
trigger_continuous = b'||>set trigger.type 5\r\n'
trigger_single_shot = b'||>set trigger.type 0\r\n'
trigger = b'||>TRIGGER ON\r\n'
last_result = b'||>GET RESULT\r\n'
light_off = b'||>SET LIGHT.DIRECT OFF OFF OFF OFF\r\n'
light_on = b'||>SET LIGHT.DIRECT ON ON ON ON\r\n' 
camera_exposure = b'||>SET CAMERA.EXPOSURE 75\r\n' 
camera_gain = b'||>SET CAMERA.GAIN 1.52\r\n' 
focus_distance = b'||>SET FOCUS.DISTANCE 40\r\n' 
dis =  b'||>GET FOCUS.DISTANCE \r\n' 


 
 
 
################################ Functions ################################
 
def activate_cognex(host_cognex, light_on):
    
    tn = telnetlib.Telnet(host_cognex)
    tn.write(light_on)
    
    return tn
 
 
 
 
 
def read_barcode(tn, camera_exposure, trigger):
    ti = time.time()
    t = 0
    
    tn.write(camera_exposure)
    tn.write(focus_distance)
    tn.write(camera_gain)
    tn.write(trigger)
 
    
    while ((time.time()-ti)<6) :
        
        # Espera até que um código de barras seja recebido
        barcode = tn.read_until(b'\n', timeout=0).strip().decode()
       
        if barcode:
            return barcode
            break
    
        
            


    
    
def deactivate_cognex(tn, light_off):
    
    tn.write(light_off)
    tn.close()

if __name__ == "__main__":
    # Ativar Cognex
    tn = activate_cognex(host_cognex, light_on)
    
    # Realizar a leitura do código de barras
    barcode = read_barcode(tn, camera_exposure, trigger)
    print(barcode)
    
    # Desativar Cognex
    deactivate_cognex(tn, light_off)


