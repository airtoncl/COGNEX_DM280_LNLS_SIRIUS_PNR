import sys, time
from time import sleep
from telnetlib import Telnet
import pickle
import random

########################## Barcode Reader (Cognex Cam) ########################## 

# host_cognex = '10.32.74.31' #old cognex DM200
host_cognex = '10.32.74.128' #cognex DM280
################################ Commands ################################

beep = b'||>beep 3 2\r\n'
ethernet_ip_enabled = b'||>get ethernet-ip.enabled\r\n'
trigger_type = b'||>get trigger.type\r\n'
trigger_continuous = b'||>set trigger.type 4\r\n'
trigger_single_shot = b'||>set trigger.type 0\r\n'
trigger = b'||>trigger on\r\n'
last_result = b'||>get result\r\n'
light_off = b'||>set light.direct 0\r\n'
light_on = b'||>set light.direct 2\r\n' #1 = internal light, 2 = external light
light_intensity = b'||>set light.direct-intensity 5\r\n' # range 0 - 13, good value = 5
#camera_exposure = b'||>set camera.exposure OFF 90 9 15\r\n'
camera_exposure = b'||>set camera.exposure OFF 90 18 4\r\n' #mudamos o ganho de 15 para 4


## 

beep = b'||>BEEP 3 2\r\n'
ethernet_ip_enabled = b'||>GET ETHERNET-IP.ENABLED\r\n'
trigger_type = b'||>GET TRIGGER.TYPE\r\n'
trigger_continuous = b'||>set trigger.type 5\r\n'
trigger_single_shot = b'||>set trigger.type 0\r\n'
trigger = b'||>TRIGGER ON\r\n'
last_result = b'||>GET RESULT\r\n'
light_off = b'||>SET LIGHT.DIRECT OFF OFF OFF OFF\r\n'
light_on = b'||>SET LIGHT.DIRECT ON ON ON ON\r\n' 
dis =  b'||>GET FOCUS.DISTANCE \r\n'

# path_parameters = '/usr/local/scripts/apps/highthroughput_system/main_complete_version_only_cryojet_used_ibira/'
path_parameters = '/ibira/lnls/beamlines/paineira/apps/ht_files/'


################################ Functions ################################

def activate_cognex(host_cognex, light_on):
    
    tn = Telnet(host_cognex)
    tn.write(light_on)
    
    return tn


def deactivate_cognex(tn, light_off):
    
    tn.write(light_off)
    tn.close()
    

def read_barcode(tn, Change_Color):
	#Make the reading of the barcode, trying to tune the camera
	#	by controling the lights on and the exposure factor, because
	#	analysing for our case, in close range measures, the lights and
	#	the exposure are the most important parameters.
    
    t = time.time()
    #print('tempo de espera do robo: ', time.time() - t)
    #Setting parameters
    f = open(path_parameters + 'store.pckl', 'rb')
    Values = pickle.load(f)
    f.close()

    #Change the color
    if Change_Color:
        if Values['pin_type'] == 'DARK':
            Values['pin_type'] = 'LIGHT'
        elif Values['pin_type'] == 'LIGHT':
            Values['pin_type'] = 'DARK'

    #Values['pin_type'] = 'LIGHT'

    camera_exposure = '||>SET CAMERA.EXPOSURE '+ str(Values['camera_exposure_value']) + '\r\n' 
    camera_exposure = camera_exposure.encode()
    camera_gain = '||>SET CAMERA.GAIN '+ str(Values['camera_gain_value']) + '\r\n' 
    camera_gain = camera_gain.encode()
    focus_distance = '||>SET FOCUS.DISTANCE '+ str(Values['focus_distance_value']) + '\r\n' 
    focus_distance = focus_distance.encode()
    trigger = b'||>TRIGGER ON\r\n'

    #sleep(0.6)

    var_light_dark = 0
    var_light_lighter = 0
    Values_light_dark = Values['light_rank_dark'].copy()
    #print(Values_light_dark)
    Values_light_dark.remove(0)
    Values_light_dark.remove(15)
    Values_light_light = Values['light_rank_lighter'].copy()
    #print(Values_light_light)
    Values_light_light.remove(0)
    Values_light_light.remove(15)

    tn.write(camera_exposure)
    tn.write(focus_distance)
    tn.write(camera_gain)
    tn.write(trigger)

    #Clean the last read in the memory of the camera
    #barcode = ''
    barcode = tn.read_until(b'\n', timeout=0.1).strip().decode()
    #print('test_barcode: ', barcode.split('\n')[0])
    while barcode != '':
        barcode = tn.read_until(b'\n', timeout=0.1).strip().decode()
        #print('barcode_while: ', barcode)
        if (time.time() - t) > 1.5:
            break
    #barcode = tn.read_eager().decode()
    barcode = ''        

    sleep(1)
    #robot_status = int(motoman_command(host_ip, host_port, robot_get_barcode_status))
    #while robot_status == 1:
    #    sleep(0.01)
    #    robot_status = int(motoman_command(host_ip, host_port, robot_get_barcode_status))
    #    #print('robot status_OUT: ', robot_status)
    t_inside = time.time()
    #print('tempo de espera: ',time.time() - t)
    #sleep(0.5)

    #tune1 = b'||>TRAIN.BRIGHT ON\r\n'
    #tune2 = b'||>TRAIN.FOCUS ON\r\n'
    #tn.write(tune1)
    #tn.write(tune2)

    for light_rank in range(5):
        #print(Values['pin_type'])
        
        var_exposure_dark = 0
        var_exposure_lighter = 0

        if Values['pin_type'] == 'DARK':
            if var_light_dark > 1:
                light = random.choice(Values_light_dark)
            else:
                light = Values_light_dark[var_light_dark]
                Values_light_dark.remove(Values_light_dark[var_light_dark])
            var_light_dark += 1
        elif Values['pin_type'] == 'LIGHT':
            if var_light_lighter > 1:
                light = random.choice(Values_light_light)
            else:
                light = Values_light_light[var_light_lighter]
                Values_light_light.remove(Values_light_light[var_light_lighter])
            var_light_lighter += 1

        light_mode, light_on = get_lights_on(light)
        Values['lights'] = light_mode
        
        #print(Values['pin_type'], light)

        ti = time.time()
        #n diffferent values of Exposure by each configuration of lights on
        for camera_exposure_rank in range(8):
            #robot_status = int(motoman_command(host_ip, host_port, robot_get_barcode_status))
            while ((time.time()-ti)<0.3) :
                # Wait until the reading of the barcode returns a valid value
                barcode = tn.read_until(b'\n', timeout=0.1).strip().decode()
        
                if barcode:
                    Values['Last_PIN'] = barcode
                    #print(Values['pin_type'])
                    #print(light)
                    #print(camera_exposure)
                    #print(focus_distance)
                    #print('tempo dentro do loop: ', time.time() - t_inside)
                    save_info(Values)
                    return barcode

            if Values['pin_type'] == 'DARK':
                if var_exposure_dark > 2:
                    value_camera_exposure = random.choice(Values['exposure_rank_dark'])
                else:
                    value_camera_exposure = Values['exposure_rank_dark'][var_exposure_dark]
                #focus_distance = set_focus(Values['focus_rank_dark'][var_exposure_dark])
                #Values['focus_distance_value'] = Values['focus_rank_dark'][var_exposure_dark]
                var_exposure_dark += 1
            elif Values['pin_type'] == 'LIGHT':
                if var_exposure_lighter > 2:
                    value_camera_exposure = random.choice(Values['exposure_rank_lighter'])
                else:
                    value_camera_exposure = Values['exposure_rank_lighter'][var_exposure_lighter]
                #focus_distance = set_focus(random.choice(Values['focus_rank_lighter']))
                #Values['focus_distance_value'] = random.choice(Values['focus_rank_lighter'])
                var_exposure_lighter += 1
            
            camera_exposure = set_camera_exposure(value_camera_exposure)
            Values['camera_exposure_value'] = value_camera_exposure

            tn.write(camera_exposure)
            tn.write(focus_distance)
            tn.write(trigger)

            #print(camera_exposure)
            #print(light_on)
            #print(focus_distance, '\n')
            ti = time.time()
            #print('robot status_INSIDE: ', robot_status)

        tn.write(light_on)
        #Change the color
        # if Values['pin_type'] == 'DARK':
        #     Values['pin_type'] = 'LIGHT'
        # elif Values['pin_type'] == 'LIGHT':
        #     Values['pin_type'] = 'DARK'

    barcode = 'NOT_READ'
    #print('tempo dentro do loop: ', time.time() - t_inside)
    return barcode



def read_barcode_check_to_measure(tn, Change_Color):
	#Make the reading of the barcode, trying to tune the camera
	#	by controling the lights on and the exposure factor, because
	#	analysing for our case, in close range measures, the lights and
	#	the exposure are the most important parameters.
    
    t = time.time()
    #print('tempo de espera do robo: ', time.time() - t)
    #Setting parameters
    f = open(path_parameters + 'store.pckl', 'rb')
    Values = pickle.load(f)
    f.close()

    #Change the color
    if Change_Color:
        if Values['pin_type'] == 'DARK':
            Values['pin_type'] = 'LIGHT'
        elif Values['pin_type'] == 'LIGHT':
            Values['pin_type'] = 'DARK'

    Values['pin_type'] = 'LIGHT'

    camera_exposure = '||>SET CAMERA.EXPOSURE '+ str(Values['camera_exposure_value']) + '\r\n' 
    camera_exposure = camera_exposure.encode()
    camera_gain = '||>SET CAMERA.GAIN '+ str(Values['camera_gain_value']) + '\r\n' 
    camera_gain = camera_gain.encode()
    focus_distance = '||>SET FOCUS.DISTANCE '+ str(Values['focus_distance_value']) + '\r\n' 
    focus_distance = focus_distance.encode()
    trigger = b'||>TRIGGER ON\r\n'

    #sleep(0.6)

    var_light_dark = 0
    var_light_lighter = 0
    Values_light_dark = Values['light_rank_dark'].copy()
    #print(Values_light_dark)
    Values_light_dark.remove(0)
    Values_light_dark.remove(15)
    Values_light_light = Values['light_rank_lighter'].copy()
    #print(Values_light_light)
    Values_light_light.remove(0)
    Values_light_light.remove(15)

    tn.write(camera_exposure)
    tn.write(focus_distance)
    tn.write(camera_gain)
    tn.write(trigger)

    #Clean the last read in the memory of the camera
    #barcode = ''
    barcode = tn.read_until(b'\n', timeout=0.1).strip().decode()
    #print('test_barcode: ', barcode.split('\n')[0])
    while barcode != '':
        barcode = tn.read_until(b'\n', timeout=0.1).strip().decode()
        #print('barcode_while: ', barcode)
        if (time.time() - t) > 1.5:
            break
    #barcode = tn.read_eager().decode()
    barcode = ''        

    sleep(1)
    #robot_status = int(motoman_command(host_ip, host_port, robot_get_barcode_status))
    #while robot_status == 1:
    #    sleep(0.01)
    #    robot_status = int(motoman_command(host_ip, host_port, robot_get_barcode_status))
    #    #print('robot status_OUT: ', robot_status)
    #t_inside = time.time()
    #print('tempo de espera: ',time.time() - t)
    #sleep(0.5)

    #tune1 = b'||>TRAIN.BRIGHT ON\r\n'
    #tune2 = b'||>TRAIN.FOCUS ON\r\n'
    #tn.write(tune1)
    #tn.write(tune2)

    for light_rank in range(5):
        #print(Values['pin_type'])
        
        var_exposure_dark = 0
        var_exposure_lighter = 0

        if Values['pin_type'] == 'DARK':
            if var_light_dark > 1:
                light = random.choice(Values_light_dark)
            else:
                light = Values_light_dark[var_light_dark]
                Values_light_dark.remove(Values_light_dark[var_light_dark])
            var_light_dark += 1
        elif Values['pin_type'] == 'LIGHT':
            if var_light_lighter > 1:
                light = random.choice(Values_light_light)
            else:
                light = Values_light_light[var_light_lighter]
                Values_light_light.remove(Values_light_light[var_light_lighter])
            var_light_lighter += 1

        light_mode, light_on = get_lights_on(light)
        Values['lights'] = light_mode
        
        #print(Values['pin_type'], light)

        ti = time.time()
        #n diffferent values of Exposure by each configuration of lights on
        for camera_exposure_rank in range(4):
            #robot_status = int(motoman_command(host_ip, host_port, robot_get_barcode_status))
            while ((time.time()-ti)<0.3) :
                # Wait until the reading of the barcode returns a valid value
                barcode = tn.read_until(b'\n', timeout=0.1).strip().decode()
        
                if barcode:
                    Values['Last_PIN'] = barcode
                    #print(Values['pin_type'])
                    #print(light)
                    #print(camera_exposure)
                    #print(focus_distance)
                    #print('tempo dentro do loop: ', time.time() - t_inside)
                    save_info(Values)
                    return barcode

            if Values['pin_type'] == 'DARK':
                if var_exposure_dark > 2:
                    value_camera_exposure = random.choice(Values['exposure_rank_dark'])
                else:
                    value_camera_exposure = Values['exposure_rank_dark'][var_exposure_dark]
                #focus_distance = set_focus(Values['focus_rank_dark'][var_exposure_dark])
                #Values['focus_distance_value'] = Values['focus_rank_dark'][var_exposure_dark]
                var_exposure_dark += 1
            elif Values['pin_type'] == 'LIGHT':
                if var_exposure_lighter > 2:
                    value_camera_exposure = random.choice(Values['exposure_rank_lighter'])
                else:
                    value_camera_exposure = Values['exposure_rank_lighter'][var_exposure_lighter]
                #focus_distance = set_focus(random.choice(Values['focus_rank_lighter']))
                #Values['focus_distance_value'] = random.choice(Values['focus_rank_lighter'])
                var_exposure_lighter += 1
            
            camera_exposure = set_camera_exposure(value_camera_exposure)
            Values['camera_exposure_value'] = value_camera_exposure

            tn.write(camera_exposure)
            tn.write(focus_distance)
            tn.write(trigger)

            #print(camera_exposure)
            #print(light_on)
            #print(focus_distance, '\n')
            ti = time.time()
            #print('robot status_INSIDE: ', robot_status)

        tn.write(light_on)
        #Change the color
        # if Values['pin_type'] == 'DARK':
        #     Values['pin_type'] = 'LIGHT'
        # elif Values['pin_type'] == 'LIGHT':
        #     Values['pin_type'] = 'DARK'

    barcode = 'NOT_READ'
    #print('tempo dentro do loop: ', time.time() - t_inside)
    return barcode

 
    
#new functions (Airton)
def save_info(Params):
	#Create 1 last row in the file of failures and sucess readings
	import pandas as pd

	if Params['pin_type'] == 'DARK':
		df = pd.read_csv(path_parameters + 'Param_dark.csv', sep=';')
	elif Params['pin_type'] == 'LIGHT':
		df = pd.read_csv(path_parameters + 'Param_lighter.csv', sep=';')
		
	df.loc[len(df.index)] = [Params['camera_exposure_value'],
								Params['camera_gain_value'],
								Params['focus_distance_value'],
								Params['lights'], 
								Params['light_mode'],
								'OK'] 
	df_ = df.groupby(df['light_mode']).count().reset_index().sort_values('camera_exposure_value', ascending=False)
	light_rank = df_['light_mode'].values.tolist()

	df_exp = df.groupby(df['camera_exposure_value']).count().reset_index().sort_values('camera_gain_value', ascending=False)
	exposure_rank = df_exp['camera_exposure_value'].values.tolist()
	

	if Params['pin_type'] == 'DARK':
		Params['light_rank_dark'] = light_rank
		Params['exposure_rank_dark'] = exposure_rank
		df.to_csv(path_parameters + 'Param_dark.csv', sep=';', index=False)

	elif Params['pin_type'] == 'LIGHT':
		Params['light_rank_lighter'] = light_rank
		Params['exposure_rank_lighter'] = exposure_rank
		df.to_csv(path_parameters + 'Param_lighter.csv', sep=';', index=False)

	f = open(path_parameters + 'store.pckl', 'wb')
	pickle.dump(Params, f)
	f.close()

def set_camera_exposure(Exposure_value):
	#Set a new value from the valid range for the exposure of the camera
	
	camera_exposure = '||>SET CAMERA.EXPOSURE ' + \
								str(Exposure_value) + '\r\n' 
	camera_exposure = camera_exposure.encode()

	return camera_exposure

def set_focus(Focus_value):
	#Set a new value from the valid range for the focus of the camera

	focus_distance = '||>SET FOCUS.DISTANCE ' + \
						str(Focus_value) + '\r\n' 
	focus_distance = focus_distance.encode()

	return focus_distance

def get_lights_on(lights_bin):
	#Get the combination of the 4 lights on of off

    light_mode = str(bin(lights_bin).replace("0b", ""))
    while len(light_mode) < 4:
        light_mode = "0" + light_mode
    light_mode = list(light_mode)

    for result in range(len(light_mode)):
        if light_mode[result] == '0':
            light_mode[result] = 'OFF'
        else:
            light_mode[result] = 'ON'
    
    light_on_mode = ''
    for result in light_mode:
        light_on_mode = light_on_mode + ' ' + result

    light_on = '||>SET LIGHT.DIRECT' + \
                 light_on_mode + '\r\n' 
    light_on = light_on.encode()
	
    return light_on_mode, light_on	