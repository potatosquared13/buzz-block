package com.example.buzzbraceletadmin;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.nfc.FormatException;
import android.nfc.NdefMessage;
import android.nfc.NdefRecord;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.tech.Ndef;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Parcelable;
import android.text.InputType;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.widget.Toolbar;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {

    public static final String ERROR_DETECTED = "No NFC tag detected!";
    public static final String WRITE_SUCCESS = "Text written to the NFC tag successfully!";
    public static final String WRITE_ERROR = "Error during writing, is the NFC tag close enough to your device?";
    NfcAdapter nfcAdapter;
    PendingIntent pendingIntent;
    IntentFilter[] writeTagFilters;
    boolean writeMode;
    Tag myTag;
    Context context;

    TextView tvNFCContent, tvName;
    Button btnWrite;
    com.example.buzzbraceletadmin.Client client;
    int i = 0;
    File[] files;


    @Override
    public void onCreate(Bundle savedInstanceState) {

        if (Build.VERSION.SDK_INT > 22)
            requestPermissions(new String[] { "android.permission.READ_EXTERNAL_STORAGE" }, 1);

        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        context = this;

        tvName              = findViewById(R.id.tvName);
        btnWrite            = findViewById(R.id.btnWrite);

        final AlertDialog.Builder builder = new AlertDialog.Builder(MainActivity.this);
        final EditText input = new EditText(MainActivity.this);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        builder.setView(input);

        //scanning dir
        String path = Environment.getExternalStorageDirectory().toString() + "/buzz/clients";
        File directory = new File(path);

        files = directory.listFiles();
        for (File f : files)
            System.out.println(f.getName());

        client = new Client(files[i]);
        tvName.setText(client.name + " (" + client.getIdentity().substring(0,8) + ")");


        btnWrite.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                    if (myTag == null) {
                        Toast.makeText(context, ERROR_DETECTED, Toast.LENGTH_LONG).show();
                    } else {
                        if(input.getParent() != null) {
                            ((ViewGroup) input.getParent()).removeView(input);
                            input.setText("");
                        }

                                try {
                                    System.out.println(client.getIdentity().substring(0, 96));
                                    write(client.getIdentity().substring(0, 96), myTag);
                                } catch (IOException | FormatException e) {
                                    Toast.makeText(context, WRITE_ERROR, Toast.LENGTH_LONG).show();
                                    e.printStackTrace();
                                }

                        Toast.makeText(context, WRITE_SUCCESS, Toast.LENGTH_LONG ).show();
                        if(i < files.length - 1) {
                            btnWrite.setEnabled(true);
                            i++;
                            client = new Client(files[i]);
                            tvName.setText(client.name + " (" + client.getIdentity().substring(0,8) + ")");
                            System.out.println(i + 1 + "/" + files.length);
                            System.out.println(client.name);
                        } else {
                            tvName.setText("No more clients");
                            Toast.makeText(context, "All Clients Written!", Toast.LENGTH_LONG).show();
                            btnWrite.setEnabled(false);
                        }
                    }
            }
        });

        nfcAdapter = NfcAdapter.getDefaultAdapter(this);
        if (nfcAdapter == null) {
            // Stop here, we definitely need NFC
            Toast.makeText(this, "This device doesn't support NFC.", Toast.LENGTH_LONG).show();
            finish();
        }

//        readFromIntent(getIntent());
        pendingIntent = PendingIntent.getActivity(this, 0, new Intent(this, getClass()).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP), 0);
        IntentFilter tagDetected = new IntentFilter(NfcAdapter.ACTION_TAG_DISCOVERED);
        tagDetected.addCategory(Intent.CATEGORY_DEFAULT);
        writeTagFilters = new IntentFilter[] { tagDetected };
    }


    /******************************************************************************
     **********************************Read From NFC Tag***************************
     ******************************************************************************/
//    private void readFromIntent(Intent intent) {
//        String action = intent.getAction();
//        if (NfcAdapter.ACTION_TAG_DISCOVERED.equals(action)
//                || NfcAdapter.ACTION_TECH_DISCOVERED.equals(action)
//                || NfcAdapter.ACTION_NDEF_DISCOVERED.equals(action)) {
//            Parcelable[] rawMsgs = intent.getParcelableArrayExtra(NfcAdapter.EXTRA_NDEF_MESSAGES);
//            NdefMessage[] msgs = null;
//            if (rawMsgs != null) {
//                msgs = new NdefMessage[rawMsgs.length];
//                for (int i = 0; i < rawMsgs.length; i++) {
//                    msgs[i] = (NdefMessage) rawMsgs[i];
//                }
//            }
//            buildTagViews(msgs);
////            tvBalance.setText(String.valueOf(node.getBalance(testclient.getIdentity().substring(0, 96))));
//        }
//    }
//    private void buildTagViews(NdefMessage[] msgs) {
//        if (msgs == null || msgs.length == 0) return;
//
//        String text = "";
//        byte[] payload = msgs[0].getRecords()[0].getPayload();
//        int languageCodeLength = payload[0] & 0063; // Get the Language Code, e.g. "en"
//
//        // Get the Text
//        text = new String(payload, languageCodeLength + 1, payload.length - languageCodeLength - 1, StandardCharsets.ISO_8859_1);
//        tvNFCContent.setText(text);
//    }

    /******************************************************************************
     **********************************Write to NFC Tag****************************
     ******************************************************************************/
    private void write(String text, Tag tag) throws IOException, FormatException {
        NdefRecord[] records = { createRecord(text) };
        NdefMessage message = new NdefMessage(records);
        // Get an instance of Ndef for the tag.
        Ndef ndef = Ndef.get(tag);
        // Enable I/O
        ndef.connect();
        // Write the message
        ndef.writeNdefMessage(message);
        // Close the connection
        ndef.close();
    }
    private NdefRecord createRecord(String text) {
        String lang       = "en";
        byte[] textBytes  = text.getBytes();
        byte[] langBytes  = lang.getBytes(StandardCharsets.ISO_8859_1);
        int    langLength = langBytes.length;
        int    textLength = textBytes.length;
        byte[] payload    = new byte[1 + langLength + textLength];

        // set status byte (see NDEF spec for actual bits)
        payload[0] = (byte) langLength;

        // copy langbytes and textbytes into payload
        System.arraycopy(langBytes, 0, payload, 1,              langLength);
        System.arraycopy(textBytes, 0, payload, 1 + langLength, textLength);

        NdefRecord recordNFC = new NdefRecord(NdefRecord.TNF_WELL_KNOWN,  NdefRecord.RTD_TEXT,  new byte[0], payload);

        return recordNFC;
    }



    @Override
    protected void onNewIntent(Intent intent) {
        setIntent(intent);
//        readFromIntent(intent);
        if (NfcAdapter.ACTION_TAG_DISCOVERED.equals(intent.getAction())){
            myTag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
        }
    }

    @Override
    public void onPause(){
        super.onPause();
        WriteModeOff();
    }

    @Override
    public void onResume(){
        super.onResume();
        WriteModeOn();
    }



    /******************************************************************************
     **********************************Enable Write********************************
     ******************************************************************************/
    private void WriteModeOn(){
        writeMode = true;
        nfcAdapter.enableForegroundDispatch(this, pendingIntent, writeTagFilters, null);
    }
    /******************************************************************************
     **********************************Disable Write*******************************
     ******************************************************************************/
    private void WriteModeOff(){
        writeMode = false;
        nfcAdapter.disableForegroundDispatch(this);
    }
}
