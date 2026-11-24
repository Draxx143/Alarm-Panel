#!/usr/bin/env python3
# Alarm panel -> KiCad 8/9 project generator (STM32F407VGT6 + ESP32-WROOM-32)
# Edit DESIGN section, run:  python3 generate_schematic.py   (output in ./out)
import math, os, uuid, zipfile, json
from collections import defaultdict, OrderedDict

STUB=200; CH=60; GAP=400
OUT=os.environ.get('OUT','.'); os.makedirs(OUT,exist_ok=True)
rnd=lambda v,m:int(math.ceil(v/m)*m)
mm=lambda v:('%.4f'%(v*0.0254)).rstrip('0').rstrip('.')
NS=uuid.UUID('6f1c2a3e-0000-4000-8000-00000000a1a1')
U=lambda k:str(uuid.uuid5(NS,k))
ROOT=U('root')

# ------------------------------------------------------------ symbols
class Sym:
    def __init__(s,**k): s.__dict__.update(k)
SYMS=OrderedDict()
def passive(name,ref,bw,plen,gfx,names=('1','2'),fp='',desc=''):
    pins=[dict(num='1',name=names[0],x=-(bw+plen),y=0,side='L',et='P',len=plen),
          dict(num='2',name=names[1],x=bw+plen,y=0,side='R',et='P',len=plen)]
    SYMS[name]=Sym(name=name,ref=ref,pins=pins,gfx=gfx,showpins=False,fp=fp,bw=bw,half=100,desc=desc)
def box(name,ref,L,R,fp='',minw=600,desc=''):
    n=max(len(L),len(R),1); half=100*math.ceil((n+1)/2)
    ml=max([len(p[1]) for p in L] or [0]); mr=max([len(p[1]) for p in R] or [0])
    w=rnd(max(minw,CH*(ml+mr)+300),200); bw=w//2; pins=[]
    for i,(num,nm,et) in enumerate(L): pins.append(dict(num=str(num),name=nm,x=-(bw+100),y=half-100-100*i,side='L',et=et,len=100))
    for i,(num,nm,et) in enumerate(R): pins.append(dict(num=str(num),name=nm,x=bw+100,y=half-100-100*i,side='R',et=et,len=100))
    SYMS[name]=Sym(name=name,ref=ref,pins=pins,gfx=[('rect',-bw,-half,bw,half)],showpins=True,fp=fp,bw=bw,half=half,desc=desc)

F_R='Resistor_SMD:R_0805_2012Metric'; F_C='Capacitor_SMD:C_0805_2012Metric'; F_TB2='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal'
tri=[('poly',[(-60,-60),(-60,60),(60,0)]),('line',60,-60,60,60)]
passive('R','R',100,50,[('rect',-100,-40,100,40)],fp=F_R)
passive('C','C',30,120,[('line',-30,-75,-30,75),('line',30,-75,30,75)],fp=F_C)
passive('CP','C',30,120,[('line',-30,-75,-30,75),('line',30,-75,30,75),('text',-110,70,'+')],names=('+','-'),fp='Capacitor_THT:CP_Radial_D8.0mm_P3.50mm')
passive('D','D',60,90,tri,names=('A','K'),fp='Diode_SMD:D_SMB')
passive('LED','D',60,90,tri+[('line',-30,90,10,130),('line',0,90,40,130)],names=('A','K'),fp='LED_SMD:LED_0805_2012Metric')
passive('PTC','F',100,50,[('rect',-100,-40,100,40),('line',-80,-80,80,80)],fp='Fuse:Fuse_1812_4532Metric')
passive('FB','FB',100,50,[('rect',-100,-40,100,40)],fp='Inductor_SMD:L_0805_2012Metric')
passive('L','L',100,50,[('rect',-100,-50,100,50),('text',-30,0,'L')],fp='Inductor_SMD:L_Bourns_SRP1245A')
passive('XTAL','Y',50,100,[('rect',-30,-70,30,70),('line',-50,-70,-50,70),('line',50,-70,50,70)],fp='Crystal:Crystal_HC49-4H_Vertical')
passive('SW','SW',60,90,[('line',-60,0,-40,0),('line',-40,0,30,40),('line',30,0,60,0)],fp='Button_Switch_THT:SW_PUSH_6mm')
passive('BAT','BT',30,120,[('line',-30,-75,-30,75),('line',30,-40,30,40),('text',-110,70,'+')],names=('+','-'),fp='Battery:BatteryHolder_Keystone_103_1x20mm')
passive('BUZZER','BZ',100,50,[('rect',-100,-60,100,60),('text',-60,-10,'BZ')],names=('+','-'),fp='Buzzer_Beeper:Buzzer_12x9.5RM7.6')
for n,f in ((2,F_TB2),(3,F_TB2.replace('-2-5.08_1x02','-3-5.08_1x03')),(5,'Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical'),(8,'Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical')):
    box('CONN_%d'%n,'J',[],[(i,str(i),'P') for i in range(1,n+1)],fp=f,minw=400)
box('CONN_2_HDR','J',[],[(1,'1','P'),(2,'2','P')],fp='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',minw=400)
box('CONN_3_HDR','J',[],[(i,str(i),'P') for i in (1,2,3)],fp='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',minw=400)
box('CONN_SMA','J',[],[(1,'SIG','P'),(2,'GND','P')],fp='Connector_Coaxial:SMA_Amphenol_901-144_Vertical',minw=400)
box('JUMPER_2','JP',[],[(1,'1','P'),(2,'2','P')],fp='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',minw=400)
box('JUMPER_2x2','JP',[],[(1,'1','P'),(2,'2','P'),(3,'3','P'),(4,'4','P')],fp='Connector_PinHeader_2.54mm:PinHeader_2x02_P2.54mm_Vertical',minw=400)
box('POT','RV',[('1','1','P'),('2','W','P')],[('3','3','P')],fp='Potentiometer_THT:Potentiometer_Bourns_3386P_Vertical',minw=400)
box('NPN_SOT23','Q',[('1','B','I')],[('3','C','P'),('2','E','P')],fp='Package_TO_SOT_SMD:SOT-23',minw=400)
box('NMOS_SOT23','Q',[('1','G','I')],[('3','D','P'),('2','S','P')],fp='Package_TO_SOT_SMD:SOT-23',minw=400)
box('PMOS_DPAK','Q',[('1','G','I')],[('2','D','P'),('3','S','P')],fp='Package_TO_SOT_SMD:TO-252-2',minw=400)
box('DUAL_DIODE','D',[('1','A1','P'),('2','K2','P')],[('3','COM','P')],fp='Package_TO_SOT_SMD:SOT-23',minw=400)
box('SRV05-4','U',[('1','IO1','P'),('2','GND','W'),('3','IO2','P')],[('6','IO4','P'),('5','VCC','W'),('4','IO3','P')],fp='Package_TO_SOT_SMD:SOT-23-6')
box('PWR_FLAG','#FLG',[],[(1,'pwr','w')],minw=200)
box('RELAY','K',[('1','COIL1','P'),('2','COIL2','P')],[('3','COM','P'),('5','NO','P'),('4','NC','P')],fp='Relay_THT:Relay_SPDT_SANYOU_SRD_Series_Form_C')
box('LM2596S','U',[(1,'VIN','W'),(5,'ON_OFF','I'),(3,'GND','W')],[(2,'OUT','O'),(4,'FB','I')],fp='Package_TO_SOT_SMD:TO-263-5_TabPin3')
box('AMS1117-3.3','U',[(3,'VIN','W'),(1,'GND','W')],[(2,'VOUT','w'),(4,'VOUT_TAB','w')],fp='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
box('LM386','U',[(1,'GAIN','P'),(2,'-IN','I'),(3,'+IN','I'),(4,'GND','W')],[(8,'GAIN2','P'),(7,'BYPASS','P'),(6,'VS','W'),(5,'VOUT','O')],fp='Package_DIP:DIP-8_W7.62mm')
box('24C256','U',[(1,'A0','I'),(2,'A1','I'),(3,'A2','I'),(4,'GND','W')],[(8,'VCC','W'),(7,'WP','I'),(6,'SCL','I'),(5,'SDA','B')],fp='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
box('PCF8574','U',[(1,'A0','I'),(2,'A1','I'),(3,'A2','I'),(16,'VCC','W'),(8,'GND','W'),(14,'SCL','I'),(15,'SDA','B'),(13,'INT','O')],
    [(4,'P0','B'),(5,'P1','B'),(6,'P2','B'),(7,'P3','B'),(9,'P4','B'),(10,'P5','B'),(11,'P6','B'),(12,'P7','B')],fp='Package_SO:SOIC-16_3.9x9.9mm_P1.27mm')
# PCA9306 dual bidirectional I2C level translator (3.3V <-> 5V for the door bus)
box('PCA9306','U',[(1,'GND','W'),(2,'VREF1','W'),(3,'SCL1','B'),(4,'SDA1','B')],
    [(8,'EN','I'),(7,'VREF2','W'),(6,'SCL2','B'),(5,'SDA2','B')],
    fp='Package_SO:VSSOP-8_2.3x2mm_P0.5mm',minw=800,desc='TI PCA9306 dual bidirectional I2C/SMBus voltage-level translator')
box('DS3231SN','U',[(2,'VCC','W'),(14,'VBAT','W'),(13,'GND','W'),(15,'SDA','B'),(16,'SCL','I'),(3,'INT_SQW','O'),(4,'RST','B'),(1,'32KHZ','O')],
    [(i,'NC','N') for i in range(5,13)],fp='Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm')
SIM_L=[(34,'VBAT','W'),(35,'VBAT','W'),(36,'GND','W'),(37,'GND','W'),(8,'GND','W'),(13,'GND','W'),(19,'GND','W'),(21,'GND','W'),(27,'GND','W'),(30,'GND','W'),(31,'GND','W'),(33,'GND','W'),
       (28,'VRTC','P'),(39,'PWRKEY','I'),(40,'VDD_EXT','w'),(41,'NETLIGHT','O'),(42,'STATUS','O'),(38,'ADC','N'),(29,'RF_SYNC','N')]
SIM_R=[(1,'UART1_TXD','O'),(2,'UART1_RXD','I'),(3,'UART1_RTS','N'),(4,'UART1_CTS','N'),(5,'UART1_DCD','N'),(6,'UART1_DTR','N'),(7,'UART1_RI','O'),
       (9,'MICP','N'),(10,'MICN','N'),(11,'SPKP','N'),(12,'SPKN','N'),(14,'SIM_DET','I'),(15,'SIM_DATA','B'),(16,'SIM_CLK','O'),(17,'SIM_RST','O'),(18,'SIM_VDD','w'),
       (20,'BT_ANT','N'),(22,'UART2_TXD','N'),(23,'UART2_RXD','N'),(24,'USB_VBUS','I'),(25,'USB_DP','B'),(26,'USB_DN','B'),(32,'GSM_ANT','P')]
box('SIM800C','U',SIM_L,SIM_R,fp='RF_GSM:SIMCom_SIM800C',minw=1600,desc='SIMCom SIM800C 42-pad LGA, pinout from SIM800C Hardware Design V1.02')
box('PMOS_SOT23','Q',[('1','G','I')],[('3','D','P'),('2','S','P')],fp='Package_TO_SOT_SMD:SOT-23',minw=400)
box('CONN_4','J',[],[(i,str(i),'P') for i in range(1,5)],fp='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',minw=400)
box('RXB61_MOD','U',[(1,'VCC','W'),(2,'GND','W')],[(3,'DATA','O'),(4,'ANT','P')],fp='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',desc='GENERIC pin numbering - match to your RXB61')
box('SIM_HOLDER_8','J',[(1,'C1_VCC','P'),(2,'C2_RST','P'),(3,'C3_CLK','P'),(4,'C4_GND','P')],[(5,'C5_GND','P'),(6,'C6_VPP','N'),(7,'C7_IO','P'),(8,'C8_DET','P')],fp='Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical',desc='8-pin SIM holder (Molex 91228 style) - replace footprint')
# nano-SIM socket. NOTE: the KiCad footprint names its pads C1..C7, CSW, DSW (not 1..8), so the
# symbol pin NUMBERS are those pad names - otherwise the symbol would not map onto the footprint.
box('SIM_NANO','J',[('C1','VCC_C1','P'),('C2','RST_C2','P'),('C3','CLK_C3','P'),('C5','GND_C5','P'),('C6','VPP_C6','N')],
    [('C7','IO_C7','P'),('DSW','DET_DSW','P'),('CSW','CSW','P')],
    fp='Connector_JAE:JAE_SIM_Card_SF72S006',desc='nano-SIM (4FF) socket JAE SF72 series, push-push, 6 contacts (C1..C7) + card detect switch DSW/CSW')
# 2x5 IDC box header used by the door board (LCD + keypad on one I2C connector)
box('CONN_2x05_IDC','J',[(1,'1','P'),(3,'3','P'),(5,'5','P'),(7,'7','P'),(9,'9','P')],
    [(2,'2','P'),(4,'4','P'),(6,'6','P'),(8,'8','P'),(10,'10','P')],
    fp='Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical',minw=600,desc='2x5 pin box header (keyed) on the main board - 6 pins used, 4 spare')
box('LCD1602','U',[(1,'VSS','W'),(2,'VDD','W'),(3,'V0','I'),(4,'RS','I'),(5,'RW','I'),(6,'E','I'),(7,'D0','N'),(8,'D1','N')],
    [(9,'D2','N'),(10,'D3','N'),(11,'D4','I'),(12,'D5','I'),(13,'D6','I'),(14,'D7','I'),(15,'A','P'),(16,'K','P')],fp='Connector_PinHeader_2.54mm:PinHeader_1x16_P2.54mm_Vertical')
esp_l="GND 3V3 EN SENSOR_VP SENSOR_VN IO34 IO35 IO32 IO33 IO25 IO26 IO27 IO14 IO12 GND IO13 SD2 SD3 CMD".split()
esp_r={38:'GND',37:'IO23',36:'IO22',35:'IO1_TXD0',34:'IO3_RXD0',33:'IO21',32:'NC',31:'IO19',30:'IO18',29:'IO5',28:'IO17',27:'IO16',26:'IO4',25:'IO0',24:'IO2',23:'IO15',22:'SD1',21:'SD0',20:'CLK',39:'GND_PAD'}
box('ESP32-WROOM-32','U',[(i+1,n,'W' if n in('GND','3V3') else 'B') for i,n in enumerate(esp_l)],
    [(k,v,'N' if v=='NC' else ('W' if v.startswith('GND') else 'B')) for k,v in esp_r.items()],fp='RF_Module:ESP32-WROOM-32')
stm="PE2 PE3 PE4 PE5 PE6 VBAT PC13 PC14 PC15 VSS VDD PH0 PH1 NRST PC0 PC1 PC2 PC3 VDD VSSA VREF+ VDDA PA0 PA1 PA2 PA3 VSS VDD PA4 PA5 PA6 PA7 PC4 PC5 PB0 PB1 PB2 PE7 PE8 PE9 PE10 PE11 PE12 PE13 PE14 PE15 PB10 PB11 VCAP1 VDD PB12 PB13 PB14 PB15 PD8 PD9 PD10 PD11 PD12 PD13 PD14 PD15 PC6 PC7 PC8 PC9 PA8 PA9 PA10 PA11 PA12 PA13 VCAP2 VSS VDD PA14 PA15 PC10 PC11 PC12 PD0 PD1 PD2 PD3 PD4 PD5 PD6 PD7 PB3 PB4 PB5 PB6 PB7 BOOT0 PB8 PB9 PE0 PE1 VSS VDD".split()
assert len(stm)==100
stype=lambda n:'W' if n[:3] in('VSS','VDD','VCA','VBA','VRE') else 'B'
box('STM32F407VGT6','U',[(i+1,stm[i],stype(stm[i])) for i in range(50)],[(i+1,stm[i],stype(stm[i])) for i in range(99,49,-1)],fp='Package_QFP:LQFP-100_14x14mm_P0.5mm',minw=1400)
STMN={i+1:stm[i] for i in range(100)}

# ------------------------------------------------------------ design
PARTS=[]; CNT=defaultdict(int); CUR=[None]
def section(n): CUR[0]=n
def add(sym,value,nets,fp=None,dnp=False):
    s=SYMS[sym]; CNT[s.ref]+=1
    ref=('#FLG%02d'%CNT[s.ref]) if s.ref=='#FLG' else '%s%d'%(s.ref,CNT[s.ref])
    p=dict(ref=ref,sym=sym,value=value,nets={str(k):v for k,v in nets.items() if v},fp=fp if fp is not None else s.fp,sec=CUR[0],dnp=dnp)
    for k in p['nets']: assert any(pp['num']==k for pp in s.pins),(sym,k)
    PARTS.append(p); return p
def two(sym,val,a,b,fp=None): return add(sym,val,{'1':a,'2':b},fp)
G='GND'; V3='+3V3'; V3W='+3V3W'; V5='+5V'
def led(src,tag,color,res='1k'):
    two('R',res,src,'LEDA_'+tag); add('LED','LED '+color,{'1':'LEDA_'+tag,'2':G})
def clamp(node): add('DUAL_DIODE','BAV99 / BAT54S clamp',{'1':G,'2':V3,'3':node})
def flag(net): add('PWR_FLAG','PWR_FLAG',{'1':net})

section('1. POWER INPUT: PTC FUSE, TVS, REVERSE-POLARITY MOSFET, ORING, BATTERY')
add('CONN_2','DC IN 13.8V 5A adapter',{1:'VIN_RAW',2:G})
two('PTC','PPTC 5A hold','VIN_RAW','VIN_F')
add('D','TVS SMBJ15A (clamp 24V)',{'1':G,'2':'VIN_F'})
add('PMOS_DPAK','IRFR5305 reverse-polarity',{'1':'RP_GATE','2':'VIN_F','3':'VIN_PROT'}); two('R','10k','RP_GATE',G)
add('D','SS56 5A adapter OR-ing',{'1':'VIN_PROT','2':'VMAIN'},fp='Diode_SMD:D_SMC')
add('CONN_2','BATTERY 12V 7Ah',{1:'BAT_IN',2:G}); two('PTC','PPTC 3A hold','BAT_IN','BAT_P')
add('D','SS54 battery OR-ing',{'1':'BAT_P','2':'VMAIN'},fp='Diode_SMD:D_SMC')
two('R','10R 2W charge-limit','VIN_PROT','CHG_A',fp='Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P15.24mm_Horizontal'); add('D','SS34',{'1':'CHG_A','2':'BAT_P'},fp='Diode_SMD:D_SMC')
two('CP','1000uF 35V','VMAIN',G,fp='Capacitor_THT:CP_Radial_D12.5mm_P5.00mm'); two('C','100nF 50V','VMAIN',G)
two('R','100k 1%','VIN_PROT','MAINS_SENSE'); two('R','22k 1%','MAINS_SENSE',G); two('R','1k','MAINS_SENSE','MAINS_ADC'); two('C','100nF','MAINS_ADC',G); clamp('MAINS_ADC')
two('R','100k 1%','BAT_P','BAT_SENSE'); two('R','22k 1%','BAT_SENSE',G); two('R','1k','BAT_SENSE','BAT_ADC'); two('C','100nF','BAT_ADC',G); clamp('BAT_ADC')
led('VIN_PROT','MAINS','red (adapter present)','4.7k')
for n in ('VIN_PROT','VMAIN','BAT_P',G): flag(n)

section('2. DC-DC (LM2596) AND LDO REGULATORS')
add('LM2596S','LM2596S-5.0',{1:'VMAIN',5:G,3:G,2:'SW5',4:V5}); two('L','33uH 4A shielded','SW5',V5)
add('D','SS54 catch',{'1':G,'2':'SW5'},fp='Diode_SMD:D_SMC'); two('CP','470uF 35V low-ESR','VMAIN',G,fp='Capacitor_THT:CP_Radial_D10.0mm_P5.00mm')
two('CP','220uF 16V low-ESR',V5,G); two('C','100nF',V5,G); add('D','TVS SMBJ5.0A',{'1':G,'2':V5})
add('LM2596S','LM2596S-ADJ (4.0V GSM)',{1:'VMAIN',5:G,3:G,2:'SW4',4:'FB4'}); two('L','33uH 4A shielded','SW4','VGSM')
add('D','SS54 catch',{'1':G,'2':'SW4'},fp='Diode_SMD:D_SMC'); two('CP','470uF 35V low-ESR','VMAIN',G,fp='Capacitor_THT:CP_Radial_D10.0mm_P5.00mm')
two('R','2.2k 1% (Vout=3.94V)','VGSM','FB4'); two('R','1k 1%','FB4',G); two('CP','470uF 10V low-ESR','VGSM',G); two('C','100nF','VGSM',G); add('D','TVS SMBJ5.0A',{'1':G,'2':'VGSM'})
add('AMS1117-3.3','AMS1117-3.3 (MCU)',{3:V5,1:G,2:V3,4:V3}); two('C','10uF 16V',V5,G); two('CP','22uF 10V tantalum',V3,G,fp='Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B'); two('C','100nF',V3,G)
add('AMS1117-3.3','AMS1117-3.3 (ESP32 only)',{3:V5,1:G,2:V3W,4:V3W}); two('C','10uF 16V',V5,G); two('CP','22uF 10V tantalum',V3W,G,fp='Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B')
two('CP','470uF 10V',V3W,G); two('C','100nF',V3W,G)
led(V5,'PWR','green (5V ok)','2.2k'); led(V3,'3V3','green (3.3V ok)','1k')
for n in (V5,'VGSM'): flag(n)

section('3. STM32F407VGT6 CORE')
# I2C: two separate hardware buses (I2C1 -> LCD, I2C3 -> keypad), moved to the door board in section 13.
#   I2C1 : PB6 = SCL1, PB7 = SDA1        (new: used to be a single shared bus)
#   I2C3 : PA8 = SCL3, PC9 = SDA3        (new: PC9 is no longer JP_FACTORY -> moved to PD7)
# JP_FACTORY moved from PC9 to PD7 because PC9 is the only usable SDA for I2C3.
M={'PA0':'ZONE1_ADC','PA1':'ZONE2_ADC','PA2':'ZONE3_ADC','PA3':'ZONE4_ADC','PA4':'DAC_OUT','PA5':'TAMPER_ADC','PA6':'RXB61_DATA',
 'PA8':'I2C3_SCL','PA9':'MCU_GSM_TX','PA10':'MCU_GSM_RX','PA13':'SWDIO','PA14':'SWCLK','PB0':'BAT_ADC','PB1':'MAINS_ADC','PB2':'BOOT1',
 'PB6':'I2C1_SCL','PB7':'I2C1_SDA','PB8':'KEYPAD_INT','PB9':'RTC_INT','PB10':'STM_U3_TX','PB11':'STM_U3_RX','PB12':'ESP_EN',
 'PB13':'ESP_IO0','PB14':'ESP_NOTIFY','PC0':'GSM_PWRKEY_CTL','PC1':'GSM_PWR_EN','PC9':'I2C3_SDA','PD7':'JP_FACTORY',
 'PD14':'GSM_STATUS','PD15':'GSM_RI',
 'PC6':'DBG_TX','PC7':'DBG_RX','PC8':'JP_SERVICE','PD8':'PGM1_CTL','PD9':'PGM2_CTL','PD10':'PGM3_CTL','PD11':'PGM4_CTL',
 'PD12':'RELAY1_CTL','PD13':'RELAY2_CTL','PE0':'SIREN1_CTL','PE1':'SIREN2_CTL','PE2':'SIREN3_CTL','PE3':'BUZZER_CTL',
 'PE4':'BTN_LEARN','PE5':'BTN_DELETE','PE6':'BTN_TEST','PE7':'SIREN_INHIBIT','PE8':'LED_GSM','PE9':'LED_ALARM','PE10':'LED_FAULT',
 'PE11':'LED_ARMED','PE13':'LED_LEARN','PE14':'LED_SERVICE','PE15':'LED_BATLOW',
 'PH0':'OSC_IN','PH1':'OSC_OUT','NRST':'NRST','BOOT0':'BOOT0','VBAT':V3,'VSSA':G,'VREF+':'VDDA','VDDA':'VDDA','VCAP1':'VCAP1','VCAP2':'VCAP2'}
nets={}
for n,name in STMN.items():
    if name=='VDD': nets[n]=V3
    elif name=='VSS': nets[n]=G
    elif name in M: nets[n]=M[name]
STM=add('STM32F407VGT6','STM32F407VGT6',nets)
add('XTAL','8MHz CL=12pF',{'1':'OSC_IN','2':'OSC_OUT'}); two('C','20pF C0G','OSC_IN',G); two('C','20pF C0G','OSC_OUT',G)
add('SW','RESET',{'1':'NRST','2':G}); two('C','100nF','NRST',G); two('R','10k','NRST',V3)
two('R','10k','BOOT0',G); add('JUMPER_2','JP_BOOT0 (install = STM32 UART bootloader)',{1:'BOOT0',2:V3}); two('R','10k','BOOT1',G)
two('C','2.2uF','VCAP1',G); two('C','2.2uF','VCAP2',G)
two('FB','Ferrite 600R/100MHz',V3,'VDDA'); two('C','100nF','VDDA',G); two('C','1uF','VDDA',G); two('CP','10uF 10V tantalum','VDDA',G,fp='Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B')
for _ in range(6): two('C','100nF',V3,G)
two('CP','10uF 10V tantalum',V3,G,fp='Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B')
add('CONN_5','SWD (3V3 SWDIO SWCLK NRST GND)',{1:V3,2:'SWDIO',3:'SWCLK',4:'NRST',5:G})
add('CONN_3_HDR','DEBUG UART6 (TX RX GND)',{1:'DBG_TX',2:'DBG_RX',3:G})
flag(G)

section('4. PROGRAMMING JUMPERS (3x) : USB-SERIAL <-> ESP32 / STM32 / LINK')
add('CONN_3_HDR','USB-SERIAL 3.3V (GND, adapter TX, adapter RX)',{1:G,2:'PROG_TX_RAW',3:'PROG_RX'})
two('R','1k','PROG_TX_RAW','PROG_TX'); clamp('PROG_TX')
add('JUMPER_2x2','JP_PROG_ESP: 1-2 and 3-4 (program ESP32 UART0)',{1:'PROG_TX',2:'ESP_RXD0',3:'ESP_TXD0',4:'PROG_RX'})
add('JUMPER_2x2','JP_PROG_STM: 1-2 and 3-4 (program STM32 USART3, BOOT0 on)',{1:'PROG_TX',2:'STM_U3_RX',3:'STM_U3_TX',4:'PROG_RX'})
add('JUMPER_2x2','JP_LINK: 1-2 and 3-4 (STM32 <-> ESP32 link)',{1:'STM_U3_TX',2:'LINK_TO_ESP',3:'STM_U3_RX',4:'LINK_FROM_ESP'})
two('R','330R','LINK_TO_ESP','ESP_U2_RX'); two('R','330R','ESP_U2_TX','LINK_FROM_ESP')
two('R','10k',V3W,'ESP_RXD0'); two('R','10k',V3,'STM_U3_RX')

section('5. GSM: BARE SIM800C CHIP + VBAT SWITCH + SIM + ANTENNA + LEVEL SHIFT')
add('SIM800C','SIM800C',{34:'GSM_VBAT',35:'GSM_VBAT',36:G,37:G,8:G,13:G,19:G,21:G,27:G,30:G,31:G,33:G,28:'GSM_VRTC',39:'GSM_PWRKEY',40:'GSM_VDDEXT',
    41:'GSM_NETLIGHT',42:'GSM_STATUS',1:'GSM_TXD',2:'GSM_RXD',7:'GSM_RI',14:'SIM_DET',15:'SIM_DATA',16:'SIM_CLK',17:'SIM_RST',18:'SIM_VDD',
    24:'GSM_USB_VBUS',25:'GSM_USB_DP_M',26:'GSM_USB_DN_M',32:'GSM_ANT'})
# VBAT power switch (hard power-cycle, SIM800C has no RESET pin)
add('PMOS_SOT23','AO3401A VBAT switch',{'1':'GSM_PG','2':'VGSM','3':'GSM_VBAT'})
two('R','100k','VGSM','GSM_PG'); two('C','100nF','GSM_PG','VGSM'); two('R','10k','GSM_PG','GSM_PG_N')
add('NPN_SOT23','BC817-40',{'1':'GSM_PWREN_B','3':'GSM_PG_N','2':G}); two('R','1k','GSM_PWR_EN','GSM_PWREN_B'); two('R','47k','GSM_PWREN_B',G)
# VBAT decoupling per SIMCom reference (Fig.5)
add('D','Zener 5.1V 500mW (MMSZ5231B)',{'1':G,'2':'GSM_VBAT'},fp='Diode_SMD:D_SOD-123')
two('CP','470uF 10V low-ESR','GSM_VBAT',G); two('CP','100uF 10V tantalum low-ESR (0.7R)','GSM_VBAT',G,fp='Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D')
two('C','10uF 10V','GSM_VBAT',G); two('C','100nF','GSM_VBAT',G); two('C','33pF C0G','GSM_VBAT',G); two('C','10pF C0G','GSM_VBAT',G)
two('C','4.7uF (VRTC backup)','GSM_VRTC',G); two('C','100nF','GSM_VDDEXT',G)
# PWRKEY transistor circuit (Fig.10)
two('R','4.7k','GSM_PWRKEY_CTL','GSM_PWRKEY_B'); two('R','47k','GSM_PWRKEY_B',G); add('NPN_SOT23','BC817-40',{'1':'GSM_PWRKEY_B','3':'GSM_PWRKEY','2':G})
# NETLIGHT LED (Fig.34)
two('R','4.7k','GSM_NETLIGHT','NL_B'); two('R','47k','NL_B',G); add('NPN_SOT23','BC817-40',{'1':'NL_B','3':'NL_C','2':G})
two('R','1k','GSM_VBAT','NL_A'); add('LED','LED green (GSM network)',{'1':'NL_A','2':'NL_C'})
# UART level shift 3.3V <-> 2.8V (VDD_EXT)
add('NMOS_SOT23','BSS138 (MCU TX -> GSM RXD)',{'1':'GSM_VDDEXT','2':'GSM_RXD','3':'MCU_GSM_TX'})
add('NMOS_SOT23','BSS138 (GSM TXD -> MCU RX)',{'1':'GSM_VDDEXT','2':'GSM_TXD','3':'MCU_GSM_RX'})
two('R','10k','GSM_VDDEXT','GSM_RXD'); two('R','10k',V3,'MCU_GSM_TX'); two('R','10k','GSM_VDDEXT','GSM_TXD'); two('R','10k',V3,'MCU_GSM_RX')
# STATUS / RI (2.8V outputs) -> STM32 FT pins PD14/PD15 (VIH = 0.45*VDD+0.3)
# SIM interface (Fig.30): 51R series, 4.7k pull-ups, ESD array, 100nF
# nano-SIM socket (JAE SF72 series) - the 8-pin holder is kept as an optional alternative, ONE of the two is fitted
add('SIM_NANO','SIM NANO-SIM SOCKET (JAE SF72, push-push) - fitted',{'C1':'SIM_VDD_H','C2':'SIM_RST_H','C3':'SIM_CLK_H','C5':G,'C6':None,'C7':'SIM_DATA_H','DSW':'SIM_DET','CSW':G})
add('SIM_HOLDER_8','SIM CARD HOLDER 8-pin (Molex 91228 style) - alternative to the nano socket',{1:'SIM_VDD_H',2:'SIM_RST_H',3:'SIM_CLK_H',4:G,5:G,7:'SIM_DATA_H',8:'SIM_DET'},dnp=True)
two('R','51R','SIM_RST','SIM_RST_H'); two('R','51R','SIM_CLK','SIM_CLK_H'); two('R','51R','SIM_DATA','SIM_DATA_H')
two('R','0R (SIM_VDD link)','SIM_VDD','SIM_VDD_H')
two('R','4.7k','SIM_DATA_H','SIM_VDD_H'); two('R','4.7k','GSM_VDDEXT','SIM_DET')
two('C','100nF','SIM_VDD_H',G); two('C','22pF','SIM_RST_H',G); two('C','22pF','SIM_CLK_H',G); two('C','22pF','SIM_DATA_H',G)
add('SRV05-4','SRV05-4 ESD (SIM lines)',{1:'SIM_RST_H',2:G,3:'SIM_CLK_H',4:'SIM_DATA_H',5:V5,6:'SIM_VDD_H'})
# antenna with matching pads (Fig.36)
two('R','0R (matching)','GSM_ANT','GSM_ANT_M'); two('C','DNP (match)','GSM_ANT',G); two('C','DNP (match)','GSM_ANT_M',G)
add('CONN_SMA','SMA GSM ANTENNA (50R trace)',{1:'GSM_ANT_M',2:G})
# USB test header for firmware upgrade/debug (Fig.23)
two('R','22R','GSM_USB_DP_M','GSM_USB_DP'); two('R','22R','GSM_USB_DN_M','GSM_USB_DN'); two('C','1uF','GSM_USB_VBUS',G)
add('CONN_4','GSM USB FW (VBUS DP DN GND) - connect 5V only for upgrade',{1:'GSM_USB_VBUS',2:'GSM_USB_DP',3:'GSM_USB_DN',4:G})

section('6. RXB61 433MHz RECEIVER (60 remotes + 8 wireless zones)')
two('FB','Ferrite 600R',V3,'RXB_VCC'); two('CP','10uF 10V tantalum','RXB_VCC',G,fp='Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B'); two('C','100nF','RXB_VCC',G)
add('RXB61_MOD','RXB61',{1:'RXB_VCC',2:G,3:'RXB_DATA_RAW',4:'ANT433'}); two('R','1k','RXB_DATA_RAW','RXB61_DATA'); two('C','100pF','RXB61_DATA',G)
add('CONN_2_HDR','ANT 433 (17.3cm wire)',{1:'ANT433',2:G})

section('7. I2C BUSES: RTC + EEPROM ON I2C1, TWO SEPARATE BUSES TO THE DOOR BOARD')
# I2C1 (PB6/PB7) = LCD bus + RTC(0x68) + EEPROM(0x50).   I2C3 (PA8/PC9) = keypad bus only.
two('R','4.7k',V3,'I2C1_SCL'); two('R','4.7k',V3,'I2C1_SDA')
add('DS3231SN','DS3231SN (0x68 on I2C1)',{2:V3,14:'RTC_VBAT',13:G,15:'I2C1_SDA',16:'I2C1_SCL',3:'RTC_INT'}); two('C','100nF',V3,G)
two('R','10k',V3,'RTC_INT'); add('BAT','CR2032',{'1':'RTC_VBAT','2':G})
add('24C256','24C256 (0x50 on I2C1)',{1:G,2:G,3:G,4:G,8:V3,7:G,6:'I2C1_SCL',5:'I2C1_SDA'}); two('C','100nF',V3,G)

section('8. ESP32-WROOM-32 (WIFI / WEB / 2 CAMERAS) - own 3.3V LDO')
add('ESP32-WROOM-32','ESP32-WROOM-32',{1:G,2:V3W,3:'ESP_EN',12:'LED_WIFI_IO',14:'ESP_IO12',15:G,25:'ESP_IO0',26:'ESP_NOTIFY',27:'ESP_U2_RX',28:'ESP_U2_TX',34:'ESP_RXD0',35:'ESP_TXD0',38:G,39:G})
two('R','10k','ESP_IO12',G); two('C','10uF',V3W,G); two('C','100nF',V3W,G)
two('R','10k',V3W,'ESP_EN'); two('C','1uF','ESP_EN',G); add('SW','ESP EN',{'1':'ESP_EN','2':G})
two('R','10k',V3W,'ESP_IO0'); add('SW','ESP BOOT (IO0)',{'1':'ESP_IO0','2':G})
two('R','1k','LED_WIFI_IO','LEDA_WIFI'); add('LED','LED blue (WiFi)',{'1':'LEDA_WIFI','2':G})

section('9. WIRED ZONES x4 + TAMPER LOOP (supervised, EOL 2.2k, filtered)')
for z in range(1,5):
    L='ZONE%d_LINE'%z; A='ZONE%d_ADC'%z
    add('CONN_2','ZONE %d (NC sensors in series, EOL 2.2k at last sensor)'%z,{1:L,2:G})
    two('R','4.7k 1%','VDDA',L); two('R','2.2k',L,A); two('C','220nF',A,G); clamp(A)
add('SRV05-4','SRV05-4 ESD (zones 1-4)',{1:'ZONE1_LINE',2:G,3:'ZONE2_LINE',4:'ZONE3_LINE',5:V5,6:'ZONE4_LINE'})
add('CONN_2','TAMPER LOOP (case switch NC + EOL 2.2k)',{1:'TAMP_LINE',2:G})
two('R','4.7k 1%','VDDA','TAMP_LINE'); two('R','2.2k','TAMP_LINE','TAMPER_ADC'); two('C','220nF','TAMPER_ADC',G); clamp('TAMPER_ADC'); add('D','ESD 5V0 (PESD5V0S1BL)',{'1':G,'2':'TAMP_LINE'},fp='Diode_SMD:D_SOD-323')
two('PTC','PPTC 1A hold','VMAIN','SENS12V'); two('CP','100uF 35V','SENS12V',G); add('D','TVS SMBJ15A',{'1':G,'2':'SENS12V'})
add('CONN_2','SENSOR POWER 12V (1)',{1:'SENS12V',2:G}); add('CONN_2','SENSOR POWER 12V (2)',{1:'SENS12V',2:G})

section('10. OUTPUTS: 4 PGM, 2 RELAYS, 3 SIRENS (hardware inhibit), BUZZER, 5V CAMERA PWR')
two('PTC','PPTC 2A hold (PGM supply)','VMAIN','PGM_12V'); add('D','TVS SMBJ15A',{'1':G,'2':'PGM_12V'})
for i in range(1,5):
    c='PGM%d_CTL'%i; g='PGM%d_G'%i; d='PGM%d_DRAIN'%i; t='PGM%d_TERM'%i
    two('R','330R',c,g); two('R','10k',g,G); add('NMOS_SOT23','AO3400A',{'1':g,'2':G,'3':d})
    two('PTC','PPTC 0.5A hold',d,t); add('D','SS14 flyback',{'1':d,'2':'PGM_12V'},fp='Diode_SMD:D_SMA')
    add('CONN_2','PGM%d (open-drain sink; load between PGM and +12V)'%i,{1:t,2:'PGM_12V'})
for i in range(1,3):
    c='RELAY%d_CTL'%i; b='RELAY%d_B'%i; k='RELAY%d_C'%i
    two('R','1k',c,b); two('R','47k',b,G); add('NPN_SOT23','BC817-40',{'1':b,'3':k,'2':G})
    add('RELAY','SRD-05VDC-SL-C',{1:V5,2:k,3:'RL%d_COM'%i,5:'RL%d_NO'%i,4:'RL%d_NC'%i}); add('D','1N4148W flyback',{'1':k,'2':V5},fp='Diode_SMD:D_SOD-123')
    add('CONN_3','RELAY %d (COM NO NC) low-voltage loads only'%i,{1:'RL%d_COM'%i,2:'RL%d_NO'%i,3:'RL%d_NC'%i})
two('PTC','PPTC 1.5A hold (sirens total)','VMAIN','SIREN_12V'); add('D','TVS SMBJ15A',{'1':G,'2':'SIREN_12V'})
for i in range(1,4):
    c='SIREN%d_CTL'%i; g='SIREN%d_G'%i; d='SIREN%d_DRAIN'%i; t='SIREN%d_TERM'%i
    two('R','330R',c,g); two('R','10k',g,G); add('NMOS_SOT23','AO3400A',{'1':g,'2':G,'3':d})
    add('D','BAT54W inhibit',{'1':g,'2':'SIREN_INHIBIT'},fp='Diode_SMD:D_SOD-323')
    two('PTC','PPTC 1A hold',d,t); add('CONN_2','SIREN %d (-, +12V)'%i,{1:t,2:'SIREN_12V'})
add('BUZZER','Active buzzer 5V',{'1':V5,'2':'BUZ_C'}); two('R','1k','BUZZER_CTL','BUZ_B'); two('R','47k','BUZ_B',G); add('NPN_SOT23','BC817-40',{'1':'BUZ_B','3':'BUZ_C','2':G})
two('PTC','PPTC 1A hold (cameras)',V5,'CAM_5V'); add('D','TVS SMBJ5.0A',{'1':G,'2':'CAM_5V'})
add('CONN_2','CAMERA 1 POWER 5V',{1:'CAM_5V',2:G}); add('CONN_2','CAMERA 2 POWER 5V',{1:'CAM_5V',2:G})

section('11. JUMPERS, BUTTONS, STATUS LEDs')
add('JUMPER_2','JP_SERVICE (install = SERVICE/repair mode)',{1:'JP_SERVICE',2:G}); two('R','10k',V3,'JP_SERVICE'); two('C','100nF','JP_SERVICE',G)
add('JUMPER_2','JP_FACTORY (install at power-up = factory reset)',{1:'JP_FACTORY',2:G}); two('R','10k',V3,'JP_FACTORY'); two('C','100nF','JP_FACTORY',G)
add('JUMPER_2','JP_SIREN_INHIBIT (install = sirens hardware-disabled)',{1:'SIREN_INHIBIT',2:G}); two('R','10k',V3,'SIREN_INHIBIT'); two('C','100nF','SIREN_INHIBIT',G)
for n,lab in (('LEARN','LEARN remote'),('DELETE','DELETE all remotes (hold)'),('TEST','TEST / silence')):
    add('SW','BTN '+lab,{'1':'BTN_%s_SW'%n,'2':G}); two('R','1k','BTN_%s_SW'%n,'BTN_'+n); two('R','10k',V3,'BTN_'+n); two('C','100nF','BTN_'+n,G)
led('LED_GSM','GSM','yellow'); led('LED_ALARM','ALARM','red'); led('LED_FAULT','FAULT','orange'); led('LED_ARMED','ARMED','green')
led('LED_LEARN','LEARN','blue (remote learning)'); led('LED_SERVICE','SERVICE','yellow'); led('LED_BATLOW','BATLOW','red (battery low)')

section('12. AUDIO: DAC -> LM386 -> SPEAKER')
two('C','10uF','DAC_OUT','AUDIO_PRE'); add('POT','10k volume',{1:'AUDIO_PRE',2:'AUDIO_IN',3:G})
add('LM386','LM386N-1',{2:G,3:'AUDIO_IN',4:G,6:V5,7:'AUDIO_BYP',5:'AUDIO_OUT'})
two('C','10uF','AUDIO_BYP',G); two('CP','100uF 16V',V5,G); two('C','100nF',V5,G); two('CP','220uF 10V','AUDIO_OUT','SPK_P')
two('R','10R','AUDIO_OUT','ZOBEL'); two('C','100nF','ZOBEL',G); add('CONN_2','SPEAKER 8R 2W',{1:'SPK_P',2:G})

section('13. DOOR BOARD (LCD + KEYPAD, EACH ON ITS OWN PCB WITH ITS OWN I2C MODULE) - ONE 2x5 BOX HEADER')
# The LCD and the keypad are NOT on this board any more: each is a separate PCB on the door, with its
# own I2C backpack (PCF8574 LCD at 0x27, PCF8574 keypad at 0x20). The only connection to the main board
# is a 2x5 (10-pin) box header; 6 of its pins are used and 4 stay spare - see section 14.
# The door board itself is delivered as two separate schematics (door_board_lcd_*.kicad_sch and
# door_board_keypad_*.kicad_sch) plus door_board_pinout.txt.
two('R','4.7k',V3,'I2C3_SCL'); two('R','4.7k',V3,'I2C3_SDA')              # pull-ups of bus 2 (bus 1 has its own)
flag('I2C1_SCL'); flag('I2C1_SDA'); flag('I2C3_SCL'); flag('I2C3_SDA')
two('PTC','PPTC 0.5A hold (door board)',V5,'DOOR_5V'); add('D','TVS SMBJ5.0A',{'1':G,'2':'DOOR_5V'})
add('PCA9306','PCA9306 #1 (I2C1: LCD backpack, 3.3V <-> 5V)',{1:G,2:V3,3:'I2C1_SCL',4:'I2C1_SDA',8:'LVL1_EN',7:'DOOR_5V',6:'LCD_SCL',5:'LCD_SDA'})
add('PCA9306','PCA9306 #2 (I2C3: keypad backpack, 3.3V <-> 5V)',{1:G,2:V3,3:'I2C3_SCL',4:'I2C3_SDA',8:'LVL2_EN',7:'DOOR_5V',6:'KP_SCL',5:'KP_SDA'})
two('R','200k 1%','DOOR_5V','LVL1_EN')      # EN tied to VREF2 through 200k (always enabled)
two('R','200k 1%','DOOR_5V','LVL2_EN')
two('R','4.7k','DOOR_5V','LCD_SCL'); two('R','4.7k','DOOR_5V','LCD_SDA')   # 5V-side pull-ups (main board side)
two('R','4.7k','DOOR_5V','KP_SCL');  two('R','4.7k','DOOR_5V','KP_SDA')
two('R','1k',V3,'KEYPAD_INT'); two('C','100nF','KEYPAD_INT',G)
two('C','100nF','DOOR_5V',G)

section('14. DOOR BOARD 2x5 BOX HEADER (J5): 6 PINS USED - 4 SPARE')
#  1 DOOR_5V (LCD backlight + both backpacks)     2 GND
#  3 LCD_SCL   4 LCD_SDA     -> I2C1 through PCA9306 #1 (LCD 0x27)
#  5 KP_SCL    6 KP_SDA      -> I2C3 through PCA9306 #2 (keypad 0x20)
#  7 KEYPAD_INT (PCF8574 /INT)   8 +3V3 (spare, for a level translator/RC on the door board)
#  9 spare   10 spare (9/10 are tied to GND so a 10-way flat cable has no floating wires)
add('CONN_2x05_IDC','DOOR BOARD 2x5 BOX HEADER - LCD PCB + KEYPAD PCB, both I2C',
    {1:'DOOR_5V',2:G,3:'LCD_SCL',4:'LCD_SDA',5:'KP_SCL',6:'KP_SDA',7:'KEYPAD_INT',8:V3,9:G,10:G})

# ------------------------------------------------------------ checks
NETS=defaultdict(list)
for p in PARTS:
    for k,n in p['nets'].items(): NETS[n].append((p['ref'],k))
print('parts',len(PARTS),'nets',len(NETS))
print('single-pin nets:',{n:v for n,v in NETS.items() if len(v)<2})
for p in PARTS:
    if p['sym'] in('R','C','CP','D','LED','PTC','FB','L') and p['nets'].get('1') and p['nets'].get('1')==p['nets'].get('2'): print('SHORTED',p['ref'])

# ------------------------------------------------------------ layout
def ext(p):
    s=SYMS[p['sym']]; le=re=s.bw+100
    for pin in s.pins:
        n=p['nets'].get(pin['num'])
        if not n: continue
        w=STUB+len(n)*CH+100
        if pin['side']=='L': le=max(le,-pin['x']+w)
        else: re=max(re,pin['x']+w)
    return le,re
def layout(parts,COLH=30000):
    cols=[[]]; y=0; cursec=None; X0=1000
    for p in parts:
        s=SYMS[p['sym']]; h=2*s.half+GAP; head=[]
        if p['sec']!=cursec: head=[('head',p['sec'])]; cursec=p['sec']
        if y+h+(600 if head else 0)>COLH and cols[-1]:
            cols.append([]); y=0
            if not head: head=[('head',p['sec']+' (cont.)')]
        for it in head: cols[-1].append(it); y+=600
        cols[-1].append(('part',p)); y+=h
    X=X0; heads=[]
    for col in cols:
        ps=[p for t,p in col if t=='part']
        if not ps: continue
        LE=rnd(max(ext(p)[0] for p in ps),100); RE=rnd(max(ext(p)[1] for p in ps),100); yy=1500
        for t,v in col:
            if t=='head': heads.append((X,yy,v)); yy+=600
            else:
                s=SYMS[v['sym']]; v['px']=X+LE; v['py']=yy+s.half; yy+=2*s.half+GAP
        X+=LE+RE+800
    return rnd(X+500,1000), rnd(COLH+3000,1000), heads, len(cols)

# ------------------------------------------------------------ optional PNG preview
# Renders the schematic the way KiCad draws it (symbol boxes + stub wires + net labels) so the
# result can be eyeballed without installing KiCad. Needs Pillow only for this preview.
def render_png(parts,heads,W,H,path,scale=1.6):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print('PIL not installed - skipping preview for',path); return
    def cv(v): return int(v*0.0254*scale*4)      # internal units -> px
    img=Image.new('RGB',(max(cv(W),40),max(cv(H),40)),'#f7f7f2')
    d=ImageDraw.Draw(img)
    try:
        f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',max(int(0.55*scale*4),6))
        fb=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',max(int(0.9*scale*4),8))
    except Exception:
        f=ImageFont.load_default(); fb=f
    for x,yv,t in heads:
        d.text((cv(x),cv(yv)),t,fill='#104a8a',font=fb)
    for p in parts:
        s=SYMS[p['sym']]; px,py=p['px'],p['py']
        d.rectangle([cv(px-s.bw),cv(py-s.half),cv(px+s.bw),cv(py+s.half)],outline='#8a1f2f',width=1)
        d.text((cv(px-s.bw),cv(py-s.half)-11),p['ref']+' '+p['value'][:46],fill='#8a1f2f',font=f)
        st=p.get('stub',STUB)
        for pin in s.pins:
            n=p['nets'].get(pin['num'])
            if not n: continue
            x=px+pin['x']; yv=py-pin['y']; left=pin['side']=='L'
            x2=x-st if left else x+st
            d.line([cv(x),cv(yv),cv(x2),cv(yv)],fill='#2b6b2b',width=1)
            if left: d.text((cv(x2)-len(n)*int(3.2*scale),cv(yv)-int(4*scale)),n,fill='#1a4d1a',font=f,anchor='la')
            else:    d.text((cv(x2),cv(yv)-int(4*scale)),n,fill='#1a4d1a',font=f,anchor='la')
    img.save(path); print('preview',path)

# --- geometry pass. Every pin becomes a horizontal stub wire with a net label at its end.
# A label must never sit on another net's wire or text (that would be a silent short / false ERC
# "net label on wire"), so real text extents are modelled and clashing parts get shorter stubs.
TW=62          # label glyph advance, in the generator's internal units (50 mil text)
LH=70          # label text height above its anchor line
def boxes(p):
    s=SYMS[p['sym']]; wires=[]; labs=[]; st=p.get('stub',STUB)
    for pin in s.pins:
        n=p['nets'].get(pin['num'])
        if not n: continue
        x=p['px']+pin['x']; yv=p['py']-pin['y']; left=pin['side']=='L'
        x2=x-st if left else x+st
        wires.append((min(x,x2),yv-20,max(x,x2),yv+20,n))
        w=len(n)*TW
        lx0,lx1=(x2-w,x2+30) if left else (x2-30,x2+w)
        labs.append((lx0,yv-LH,lx1,yv,n))
    return wires,labs
def hit(a,b): return not (a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1])
def problems(p):
    wires,labs=boxes(p); bad=[]
    for i,(x0,y0,x1,y1,n) in enumerate(labs):
        for j,w in enumerate(wires):
            if j!=i and hit((x0,y0,x1,y1),w): bad.append((n,w[4]))
        for j,(a0,b0,a1,b1,m) in enumerate(labs):
            if j!=i and n!=m and hit((x0,y0,x1,y1),(a0,b0,a1,b1)): bad.append((n,m))
    return bad
def fix_geometry(parts):
    bad=[p for p in parts if problems(p)]
    for p in bad:
        for st in (180,140,100,60):
            p['stub']=st
            if not problems(p): break
    left=[(p['ref'],problems(p)) for p in parts if problems(p)]
    print('layout geometry clashes left:',left)
    return left

# ------------------------------------------------------------ KiCad writers
def q(s): return '"%s"'%str(s).replace('\\','\\\\').replace('"','\\"')
FS='(effects (font (size 1.27 1.27)))'; FSH='(effects (font (size 1.27 1.27)) hide)'
ETM={'P':'passive','I':'input','O':'output','B':'bidirectional','W':'power_in','w':'power_out','N':'no_connect'}
def lib_symbol(s,prefix=''):
    o=['\t\t(symbol %s'%q(prefix+s.name)]
    if not s.showpins: o.append('\t\t\t(pin_numbers hide)\n\t\t\t(pin_names (offset 0) hide)')
    else: o.append('\t\t\t(pin_names (offset 0.5))')
    if s.ref=='#FLG': o.append('\t\t\t(power)')
    o.append('\t\t\t(exclude_from_sim no)\n\t\t\t(in_bom %s)\n\t\t\t(on_board %s)'%(('no','no') if s.ref=='#FLG' else ('yes','yes')))
    top=mm(s.half+60)
    o.append('\t\t\t(property "Reference" %s (at 0 %s 0) %s)'%(q(s.ref),top,FS))
    o.append('\t\t\t(property "Value" %s (at 0 -%s 0) %s)'%(q(s.name),top,FS))
    o.append('\t\t\t(property "Footprint" %s (at 0 0 0) %s)'%(q(s.fp),FSH))
    o.append('\t\t\t(property "Datasheet" "" (at 0 0 0) %s)'%FSH)
    o.append('\t\t\t(property "Description" %s (at 0 0 0) %s)'%(q(s.desc),FSH))
    o.append('\t\t\t(symbol %s'%q(s.name+'_0_1'))
    for g in s.gfx:
        if g[0]=='rect': o.append('\t\t\t\t(rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type default)) (fill (type background)))'%tuple(mm(v) for v in g[1:5]))
        elif g[0]=='line': o.append('\t\t\t\t(polyline (pts (xy %s %s) (xy %s %s)) (stroke (width 0.254) (type default)) (fill (type none)))'%tuple(mm(v) for v in g[1:5]))
        elif g[0]=='poly':
            pts=g[1]+[g[1][0]]; o.append('\t\t\t\t(polyline (pts %s) (stroke (width 0.254) (type default)) (fill (type outline)))'%' '.join('(xy %s %s)'%(mm(a),mm(b)) for a,b in pts))
        elif g[0]=='text': o.append('\t\t\t\t(text %s (at %s %s 0) %s)'%(q(g[3]),mm(g[1]),mm(g[2]),FS))
    o.append('\t\t\t)')
    o.append('\t\t\t(symbol %s'%q(s.name+'_1_1'))
    for pin in s.pins:
        ang=0 if pin['side']=='L' else 180
        o.append('\t\t\t\t(pin %s line (at %s %s %d) (length %s) (name %s %s) (number %s %s))'%(ETM[pin['et']],mm(pin['x']),mm(pin['y']),ang,mm(pin['len']),q(pin['name'] or '~'),FS,q(pin['num']),FS))
    o.append('\t\t\t)\n\t\t)'); return '\n'.join(o)
def kicad_sch(parts,heads,W,H,root,title,rev,project,com1,com2):
    o=['(kicad_sch','\t(version 20231120)','\t(generator "eeschema")','\t(generator_version "8.0")','\t(uuid %s)'%q(root),
       '\t(paper "User" %s %s)'%(mm(W),mm(H)),
       '\t(title_block (title %s) (rev %s) (comment 1 %s) (comment 2 %s))'%(q(title),q(rev),q(com1),q(com2)),
       '\t(lib_symbols']
    for s in SYMS.values(): o.append(lib_symbol(s,'alarm_panel:'))
    o.append('\t)')
    for x,yv,t in heads:
        o.append('\t(text %s (exclude_from_sim no) (at %s %s 0) (effects (font (size 2.54 2.54) bold) (justify left bottom)) (uuid %s))'%(q(t),mm(x),mm(yv),q(U('h%d%d'%(x,yv)))))
    for i,p in enumerate(parts):
        s=SYMS[p['sym']]; px,py=p['px'],p['py']; flagp=s.ref=='#FLG'
        o.append('\t(symbol (lib_id %s) (at %s %s 0) (unit 1) (exclude_from_sim no) (in_bom %s) (on_board %s) (dnp %s) (uuid %s)'%(q('alarm_panel:'+s.name),mm(px),mm(py),'no' if flagp else 'yes','no' if flagp else 'yes','yes' if p.get('dnp') else 'no',q(U('s'+p['ref']))))
        o.append('\t\t(property "Reference" %s (at %s %s 0) %s)'%(q(p['ref']),mm(px),mm(py-s.half-100),FSH if flagp else FS))
        o.append('\t\t(property "Value" %s (at %s %s 0) %s)'%(q(p['value']),mm(px),mm(py+s.half+100),FSH if flagp else FS))
        o.append('\t\t(property "Footprint" %s (at %s %s 0) %s)'%(q(p['fp']),mm(px),mm(py),FSH))
        o.append('\t\t(property "Datasheet" "" (at %s %s 0) %s)'%(mm(px),mm(py),FSH))
        for pin in s.pins: o.append('\t\t(pin %s (uuid %s))'%(q(pin['num']),q(U('p%s_%s'%(p['ref'],pin['num'])))))
        o.append('\t\t(instances (project %s (path %s (reference %s) (unit 1))))\n\t)'%(q(project),q('/'+root),q(p['ref'])))
        for pin in s.pins:
            n=p['nets'].get(pin['num'])
            if not n: continue
            x=px+pin['x']; yy=py-pin['y']; left=pin['side']=='L'; st=p.get('stub',STUB); x2=x-st if left else x+st
            o.append('\t(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid %s))'%(mm(x),mm(yy),mm(x2),mm(yy),q(U('w%s_%s'%(p['ref'],pin['num'])))))
            o.append('\t(label %s (at %s %s %d) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid %s))'%(q(n),mm(x2),mm(yy),180 if left else 0,'right' if left else 'left',q(U('l%s_%s'%(p['ref'],pin['num'])))))
    o.append('\t(sheet_instances (path "/" (page "1")))\n)')
    return '\n'.join(o)+'\n'
def kicad_sym():
    o=['(kicad_symbol_lib','\t(version 20231120)','\t(generator "kicad_symbol_editor")','\t(generator_version "8.0")']
    for s in SYMS.values(): o.append(lib_symbol(s,''))
    o.append(')'); return '\n'.join(o)+'\n'
def emit(parts,folder,fname,libname,title,rev,com1,com2,COLH=30000,png=False):
    W,H,heads,ncol=layout(parts,COLH); fix_geometry(parts)
    if png: render_png(parts,heads,W,H,OUT+'/'+folder+'.png')
    P=OUT+'/'+folder; os.makedirs(P,exist_ok=True)
    root=U('root:'+fname)
    open(P+'/'+fname+'.kicad_sch','w').write(kicad_sch(parts,heads,W,H,root,title,rev,fname,com1,com2))
    open(P+'/'+fname+'.kicad_sym','w').write(kicad_sym())
    open(P+'/sym-lib-table','w').write('(sym_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s.kicad_sym")(options "")(descr "Alarm panel symbols"))\n)\n'%(libname,fname))
    json.dump({"meta":{"filename":fname+".kicad_pro","version":1},"schematic":{"drawing":{"default_text_size":50.0}}},open(P+'/'+fname+'.kicad_pro','w'),indent=2)
    print('sheet',folder,'mm',mm(W),mm(H),'cols',ncol,'parts',len(parts))
    return P

MAIN='alarm_panel'
emit(PARTS,MAIN,MAIN,'alarm_panel','Central Alarm Panel - STM32F407VGT6 + ESP32-WROOM-32','3',
     'Net-label based schematic (generated) - rev 3: nano-SIM socket, two I2C buses to the door board',
     'Rev 3 changes: nano-SIM socket J6 (J7 = optional 8-pin holder, DNP); LCD and keypad moved to the door board and reached through one 2x5 box header J30 (sections 13-14); I2C1 (PB6/PB7) = LCD + RTC + EEPROM, I2C3 (PA8/PC9) = keypad; JP_FACTORY moved from PC9 to PD7; PCA9306 5V level shifters added')
MAIN_PARTS=PARTS[:]

# ------------------------------------------------------------ DOOR BOARD (two separate small PCBs)
PARTS=[]
section('DOOR BOARD - LCD PCB (1602 LCD + I2C backpack PCF8574, 0x27)')
two('R','4.7k','DOOR_5V','LCD_SCL'); two('R','4.7k','DOOR_5V','LCD_SDA')
add('PCF8574','PCF8574 LCD backpack (0x27)',{1:'A0',2:'A1',3:'A2',16:'DOOR_5V',8:G,14:'LCD_SCL',15:'LCD_SDA',4:'LCD_RS',6:'LCD_E',7:'LCD_BL_CTL',9:'LCD_D4',10:'LCD_D5',11:'LCD_D6',12:'LCD_D7'}); two('C','100nF','DOOR_5V',G)
for n in ('A0','A1','A2'): two('R','0R (address strap)',n,G)
add('LCD1602','LCD 2x16 (RW tied to GND: write-only, 5V-safe)',{1:G,2:'DOOR_5V',3:'LCD_V0',4:'LCD_RS',5:G,6:'LCD_E',11:'LCD_D4',12:'LCD_D5',13:'LCD_D6',14:'LCD_D7',15:'LCD_A',16:'LCD_K'})
two('R','100R','DOOR_5V','LCD_A'); two('R','1k','LCD_BL_CTL','LCD_BL_B'); add('NPN_SOT23','BC817-40',{'1':'LCD_BL_B','3':'LCD_K','2':G}); two('R','47k','LCD_BL_B',G)
add('POT','10k contrast',{1:'DOOR_5V',2:'LCD_V0',3:G}); two('C','100nF','DOOR_5V',G)
# J1 carries the same 10-pin pinout as J30 on the main board; only the pins this PCB needs are used
add('CONN_2x05_IDC','J1 = 2x5 BOX HEADER (same pinout as main J30) - LCD board uses 1,2,3,4',{1:'DOOR_5V',2:G,3:'LCD_SCL',4:'LCD_SDA'})
for n in ('DOOR_5V','LCD_SCL','LCD_SDA','LCD_RS','LCD_E','KEYPAD_INT','GND'): flag(n)
two('C','100nF','DOOR_5V',G); two('CP','10uF 10V','DOOR_5V',G)
LCD_PARTS=PARTS[:]

PARTS=[]
section('DOOR BOARD - KEYPAD PCB (4x4 keypad + I2C backpack PCF8574, 0x20)')
two('R','4.7k','DOOR_5V','KP_SCL'); two('R','4.7k','DOOR_5V','KP_SDA')
add('PCF8574','PCF8574 keypad backpack (0x20)',{1:'A0',2:'A1',3:'A2',16:'DOOR_5V',8:G,14:'KP_SCL',15:'KP_SDA',13:'KEYPAD_INT',4:'KP_P0',5:'KP_P1',6:'KP_P2',7:'KP_P3',9:'KP_P4',10:'KP_P5',11:'KP_P6',12:'KP_P7'})
two('R','0R (address strap)','A0','DOOR_5V')      # 0x20: A0 high
two('R','0R (address strap)','A1',G); two('R','0R (address strap)','A2',G)
two('R','10k','DOOR_5V','KEYPAD_INT'); two('C','100nF','DOOR_5V',G)
add('CONN_8','KEYPAD 4x4 (rows P0-3, cols P4-7)',{i:'KP_P%d'%(i-1) for i in range(1,9)})
# J1 carries the same 10-pin pinout as J30 on the main board; only the pins this PCB needs are used
add('CONN_2x05_IDC','J1 = 2x5 BOX HEADER (same pinout as main J30) - keypad board uses 1,2,5,6,7',{1:'DOOR_5V',2:G,5:'KP_SCL',6:'KP_SDA',7:'KEYPAD_INT'})
for n in ('DOOR_5V','KP_SCL','KP_SDA','KEYPAD_INT','GND'): flag(n)
two('C','100nF','DOOR_5V',G); two('CP','10uF 10V','DOOR_5V',G)
KP_PARTS=PARTS[:]

emit(LCD_PARTS,'door_board_lcd','door_board_lcd','door_board_lcd','Door Board - LCD PCB (1602 + PCF8574 I2C backpack)','1',
     'Separate PCB - LCD on the door, its own PCF8574 I2C backpack (0x27)','5V board; connects to the main board with a 2x5 box header (same pinout as J30, pins 1-4 used)',COLH=5000,png=True)
emit(KP_PARTS,'door_board_keypad','door_board_keypad','door_board_keypad','Door Board - KEYPAD PCB (4x4 + PCF8574 I2C backpack)','1',
     'Separate PCB - keypad on the door, its own PCF8574 I2C backpack (0x20)','5V board; connects to the main board with a 2x5 box header (same pinout as J30, pins 1,2,5,6,7 used)',COLH=5000,png=True)

# ------------------------------------------------------------ BOM + pin map
PARTS=MAIN_PARTS
bom=defaultdict(list)
for p in PARTS:
    if p['sym']!='PWR_FLAG': bom[(p['sym'],p['value']+('  [DNP - NOT FITTED]' if p.get('dnp') else ''))].append(p['ref'])
with open(OUT+'/BOM.txt','w',encoding='utf-8') as f:
    f.write('BOM (qty / value / symbol / refs)  - generated from the schematic\n'+'='*80+'\n')
    for (sym,val),refs in sorted(bom.items(),key=lambda kv:(SYMS[kv[0][0]].ref,kv[0][1])): f.write('%-3d  %-52s %-16s %s\n'%(len(refs),val,sym,' '.join(refs)))
    f.write('\nTotal parts: %d\n'%sum(len(v) for v in bom.values()))
with open(OUT+'/STM32_ESP32_pin_map.txt','w',encoding='utf-8') as f:
    f.write('STM32F407VGT6 (LQFP-100) pin map\n'+'='*60+'\n')
    for k in sorted(STM['nets'],key=int): f.write('pin %-3s %-6s -> %s\n'%(k,STMN[int(k)],STM['nets'][k]))
