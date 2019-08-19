''' Code Inspired by http://github.com/tito 's NFC gist
This is a complete implementation allowing for NFC tag or p2p detection
Allows you to create any type of NdefRecord using functions like
`create_RTDURI(uri)`
This is the Android implementatoin of NFC Scanning using the
built in NFC adapter of some android phones.
'''

from kivy.app import App
from kivy.clock import Clock
#Detect which platform we are on
from kivy.logger import Logger
from kivy.utils import platform
if platform != 'android':
    raise ImportError
import threading

from nfc_manager import NFCBase
from jnius import autoclass, cast
from android.runnable import run_on_ui_thread
from android import activity

BUILDVERSION = autoclass('android.os.Build$VERSION').SDK_INT
NfcAdapter = autoclass('android.nfc.NfcAdapter')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
JString = autoclass('java.lang.String')
Charset = autoclass('java.nio.charset.Charset')
locale = autoclass('java.util.Locale')
Intent = autoclass('android.content.Intent')
IntentFilter = autoclass('android.content.IntentFilter')
PendingIntent = autoclass('android.app.PendingIntent')
Ndef = autoclass('android.nfc.tech.Ndef')
NdefRecord = autoclass('android.nfc.NdefRecord')
NdefMessage = autoclass('android.nfc.NdefMessage')

app = None



class ScannerAndroid(NFCBase):
    ''' This is the class responsible for handling the interace with the
    Android NFC adapter. See Module Documentation for deatils.
    '''

    name = 'NFCAndroid'

    def nfc_init(self):
        ''' This is where we initialize NFC adapter.
        '''
        # Initialize NFC
        global app
        app = App.get_running_app()

        # Make sure we are listening to new intent
        activity.bind(on_new_intent=self.on_new_intent)

        # Configure nfc
        self.j_context = context = PythonActivity.mActivity
        self.nfc_adapter = NfcAdapter.getDefaultAdapter(context)
        # Check if adapter exists
        if not self.nfc_adapter:
            return False

        # specify that we want our activity to remain on top whan a new intent
        # is fired
        self.nfc_pending_intent = PendingIntent.getActivity(context, 0,
            Intent(context, context.getClass()).addFlags(
                Intent.FLAG_ACTIVITY_SINGLE_TOP), 0)

        # Filter for different types of action, by default we enable all.
        # These are only for handling different tags when app is in foreground
        self.ndef_detected = IntentFilter(NfcAdapter.ACTION_NDEF_DISCOVERED)
        self.tech_detected = IntentFilter(NfcAdapter.ACTION_TECH_DISCOVERED)
        self.tag_detected = IntentFilter(NfcAdapter.ACTION_TAG_DISCOVERED)

        # setup tag discovery for ourt tag type
        try:
            self.ndef_detected.addCategory(Intent.CATEGORY_DEFAULT)
            # setup the foreground dispatch to detect all mime types
            self.ndef_detected.addDataType('*/*')

            self.tech_detected.addCategory(Intent.CATEGORY_DEFAULT)
            self.tech_detected.addDataType('*/*')

            self.tag_detected.addCategory(Intent.CATEGORY_DEFAULT)
            self.tag_detected.addDataType('*/*')

            # setup exchange filters, this is a list of actions that the application
            # will listen for.
            self.ndef_exchange_filters = [self.ndef_detected, self.tech_detected,
                                          self.tag_detected]
        except Exception as err:
            raise Exception(repr(err))

        self.ndef_tech_list = [
            ['android.nfc.tech.Ndef'],
            ['android.nfc.tech.NfcA'],
            ['android.nfc.tech.NfcB'],
            ['android.nfc.tech.NfcV'],
            ['android.nfc.tech.IsoDep'],
            ['android.nfc.tech.MifareUltralight'],
            ['android.nfc.tech.NdefFormattable'] ]
        self.nfc_enable()
        self.on_new_intent(PythonActivity.getIntent())
        return True

    def get_ndef_details(self, tag):
        ''' Get all the details from the tag.
        '''
        details = {}

        #print 'id'
        details['uid'] = ':'.join(['{:02x}'.format(bt & 0xff) for bt in tag.getId()])
        #print 'technologies'
        details['Technologies'] = tech_list = [tech.split('.')[-1] for tech in tag.getTechList()]
        #print 'get NDEF tag details'
        ndefTag = cast('android.nfc.tech.Ndef', Ndef.get(tag))
        #print 'tag size'
        details['MaxSize'] = ndefTag.getMaxSize()
        #details['usedSize'] = '0'
        #print 'is tag writable?'
        details['writable'] = ndefTag.isWritable()
        #print 'Data format'
        # Can be made readonly
        # get NDEF message details
        ndefMesg = ndefTag.getCachedNdefMessage()
        # get size of current records
        details['consumed'] = len(ndefMesg.toByteArray()) if ndefMesg else 0
        #print 'tag type'
        details['Type'] = ndefTag.getType()

        # check if tag is empty
        if not ndefMesg:
            details['Message'] = None
            return details

        ndefrecords =  ndefMesg.getRecords()
        length = len(ndefrecords)
        #print 'length', length
        # will contain the NDEF record types
        recTypes = []
        for record in ndefrecords:
            recTypes.append({
                'type': ''.join(map(chr, record.getType())),
                'payload': ''.join(map(chr, record.getPayload()))
                })

        details['recTypes'] = recTypes

        return details

    def on_new_intent(self, intent):
        ''' This functions is called when the application receives a
        new intent, for the ones the application has registered previously,
        either in the manifest or in the foreground dispatch setup in the
        nfc_init function above.
        '''
        #print 'on_new_intent', intent
        app = App.get_running_app()
        #if not app.status == 'listening':
        #    return

        action_list = (NfcAdapter.ACTION_TAG_DISCOVERED,
                       NfcAdapter.ACTION_TECH_DISCOVERED,
                       NfcAdapter.ACTION_NDEF_DISCOVERED,)

        # get TAG
        extra_tag =  intent.getParcelableExtra(NfcAdapter.EXTRA_TAG)
        if app.mode != 'write' and not extra_tag:
            return

        tag = cast('android.nfc.Tag', extra_tag)

        try:
            details = self.get_ndef_details(tag)
        except Exception:
            app.show_info('Unknown or INVALID TAG')
            print(err)
            Clock.schedule_once(lambda dt:app._pause(), 2)
            return

        if intent.getAction() not in action_list:
            return

        app.tag_discovered(details)
        if app.mode == 'write':
            self.nfc_write_tag(tag, app.data)

    def nfc_disable(self):
        '''Disable app from handling tags.
        '''
        self.disable_foreground_dispatch()

    def nfc_enable(self):
        '''Enable app to handle tags when app in foreground.
        '''
        self.enable_foreground_dispatch()

    def create_RTDURI(self, URI):
        '''Create RTD_URI to be written to the tag
        '''
        # If JellyBean or higher android version then use newer api.
        if not URI:
            URI = "http://google.com"
        if URI.lower().startswith('http://'):
            URI = URI[7:]
        if BUILDVERSION >= 14:
            rtdUriRecord = NdefRecord.createUri(JString('http://' + URI));
        else:
            # Create record manually.
            uriField = JString(URI).getBytes(Charset.forName("US-ASCII"))
            # add 1 for the URI Prefix
            payload = []
            # prefixes http://www. to the URI
            payload.append(0x01)
            # append URI to payload
            payload.extend(uriField)
            rtdUriRecord = NdefRecord(
                NdefRecord.TNF_WELL_KNOWN, NdefRecord.RTD_URI, '', payload)
        return rtdUriRecord

    def create_AAR(self):
        '''Create the record responsible for linking our application to the tag.
        '''
        return NdefRecord.createApplicationRecord(JString("org.kivy.kivy"))

    def create_TNF_EXTERNAL(self, data):
        '''Create our actual payload record.
        '''
        if BUILDVERSION >= 14:
            domain = "com.kivy"
            stype = "externalType"
            extRecord = NdefRecord.createExternal(domain, stype, data)
        else:
            # Creating the NdefRecord manually:
            extRecord = NdefRecord(
                NdefRecord.TNF_EXTERNAL_TYPE,
                "com.kivy:externalType",
                '',
                data)
        return extRecord

    def create_ndef_message(self, *recs):
        ''' Create the Ndef message that will written to tag
        '''
        return NdefMessage([record for record in recs if record])

    def nfc_write_tag(self, tag, data):
        '''Write data to tag. This attempts to write a URI record, AAR,
        the actual payload. Unfortunately ntag203 does not have enough
        space and including both AAR and URI leads to there being not
        much space left for the actual payload. To try and get more
        space for actual payload you can experiment with removing one
        of these AAR/URI below.
        '''
        record = None
        # if BUILDVERSION >= 14:
        #     # if jellybean
        #     # create Androud Application Record
        #     record = self.create_AAR()
        # else:
        #     # older android versions can't  use AAR
        #     # Create NdefRecord type: RTD_URI
        record = self.create_RTDURI(data)

        payload = None
        # Create the actual payload
        payload =  self.create_TNF_EXTERNAL(data)

        # create the ndef mesage
        message = self.create_ndef_message(record, payload)

        # write the actual message
        size = len(message.toByteArray())

        ndef = Ndef.get(tag)

        if not ndef.isWritable():
            return app.show_info('This tag is not writable.')

        max_size = ndef.getMaxSize()
        if size > max_size:
            # not enough space to write date
            app.show_info('Not enugh space on tag! Trim your data.\n'
                          '{}/{}'.format(size, max_size))
            return

        #def delayed(ndef, message):
        try:
            ndef.connect()
            ndef.writeNdefMessage(message)
            ndef.close()
            Clock.schedule_once(lambda dt: app.show_info('Tag written to successfully'))
            app.mode = 'idle'
        except Exception as err:
            Clock.schedule_once(lambda dt: app.show_info(unicode(err)))

        # tag written successfully

        #threading.Thread(target=delayed, args=(ndef, message)).start()


    @run_on_ui_thread
    def disable_foreground_dispatch(self):
        '''Disable foreground dispatch when app is paused.
        '''
        self.nfc_adapter.disableForegroundDispatch(self.j_context)

    @run_on_ui_thread
    def enable_foreground_dispatch(self):
        '''Start listening for new tags
        '''
        if app.status == 'paused':
            return
        self.nfc_adapter.enableForegroundDispatch(self.j_context,
            self.nfc_pending_intent, self.ndef_exchange_filters, self.ndef_tech_list)
        #self.on_new_intent(PythonActivity.getIntent())

    @run_on_ui_thread
    def _nfc_enable_ndef_exchange(self, data):
        # Enable p2p exchange
        # Create record
        ndef_record = NdefRecord(
                NdefRecord.TNF_MIME_MEDIA,
                'text/plain', '', data)

        # Create message
        ndef_message = NdefMessage([ndef_record])

        # Enable ndef push
        self.nfc_adapter.enableForegroundNdefPush(self.j_context, ndef_message)

        # Enable dispatch
        self.nfc_adapter.enableForegroundDispatch(self.j_context,
                self.nfc_pending_intent, self.ndef_exchange_filters, [])

    @run_on_ui_thread
    def _nfc_disable_ndef_exchange(self):
        # Disable p2p exchange
        self.nfc_adapter.disableForegroundNdefPush(self.j_context)
        self.nfc_adapter.disableForegroundDispatch(self.j_context)

    def nfc_enable_exchange(self, data):
        '''Enable Ndef exchange for p2p
        '''
        self._nfc_enable_ndef_exchange()

    def nfc_disable_exchange(self):
        ''' Disable Ndef exchange for p2p
        '''
        self._nfc_disable_ndef_exchange()
