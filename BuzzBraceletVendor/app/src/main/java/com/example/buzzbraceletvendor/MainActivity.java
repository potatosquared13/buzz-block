package com.example.buzzbraceletvendor;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.nfc.NdefMessage;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Parcelable;
import android.text.InputType;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;


import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;

public class MainActivity extends Activity {

    public static final String WRITE_SUCCESS = "Transaction Successful!";
    public static final String WRITE_BLACKLIST = "Failed. Account Blacklisted!";
    public static final String WRITE_NO_FUNDS = "Failed. Insufficient Funds!";
    public static final String WRITE_FAILED = "Unable to send transaction!";

    NfcAdapter nfcAdapter;
    PendingIntent pendingIntent;
    IntentFilter[] writeTagFilters;
    boolean writeMode;
    Tag myTag;
    Context context;

    TextView tvNFCContent, tvBalance, tvToolBar, tvStatus;
    ImageView ivTag;
    Button btnSendTransaction;
    Node node;
    int returnCode;

//    String[] values = new String[] { node.getTransactions().toString()};
//    ArrayList<String> list = new ArrayList<String>();
    ListView lvList;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        //Permissions
        if (Build.VERSION.SDK_INT > 22)
            requestPermissions(new String[] {"android.permission.INTERNET",
                    "android.permission.ACCESS_WIFI_STATE",
                    "android.permission.READ_EXTERNAL_STORAGE",
                    "android.permission.WRITE_EXTERNAL_STORAGE"}, 1);
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        context = this;
        tvNFCContent        = findViewById(R.id.tvNFCContents);
        btnSendTransaction  = findViewById(R.id.btnSendTransaction);
        tvBalance           = findViewById(R.id.tvBalance);
        lvList              = findViewById(R.id.lvList);
        tvToolBar           = findViewById(R.id.tvToolBar);
        tvStatus            = findViewById(R.id.tvStatus);
        ivTag               = findViewById(R.id.ivTag);

        final AlertDialog.Builder builder = new AlertDialog.Builder(MainActivity.this);
        final EditText input = new EditText(MainActivity.this);
        input.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        builder.setView(input);
        btnSendTransaction.setVisibility(View.INVISIBLE);
        tvBalance.setVisibility(View.INVISIBLE);
        tvNFCContent.setVisibility(View.INVISIBLE);

        ivTag.setVisibility(View.VISIBLE);
        tvStatus.setVisibility(View.VISIBLE);

        /**PAYMENT**/
        btnSendTransaction.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
            if (input.getParent() != null) {
                ((ViewGroup) input.getParent()).removeView(input);
                input.setText("");
            }
            builder.setTitle("Payment");

            // Set up the buttons
            builder.setPositiveButton("OK", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    double amount = Double.parseDouble(input.getText().toString());
                    returnCode = node.sendPayment(tvNFCContent.getText().toString(), amount);


                    if(returnCode == 0) {
                        Toast.makeText(context, WRITE_SUCCESS, Toast.LENGTH_LONG ).show();
                    } else if(returnCode == 1) {
                        Toast.makeText(context, WRITE_BLACKLIST, Toast.LENGTH_LONG ).show();
//                        tvStatus.setText("BLACKLISTED");
                    } else if (returnCode == 3) {
                        Toast.makeText(context, WRITE_NO_FUNDS, Toast.LENGTH_LONG ).show();
                    } else {
                        Toast.makeText(context, WRITE_FAILED, Toast.LENGTH_LONG ).show();
//                        tvStatus.setText("Write Failed");
                    }

                    tvNFCContent.setText("");
                    tvBalance.setText("");
                    btnSendTransaction.setVisibility(View.INVISIBLE);
                    ivTag.setVisibility(View.VISIBLE);
                    dialog.cancel();
                }
            });
            builder.setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    dialog.cancel();
                }
            });
            builder.show();
            }
        });

        //Check if NFC Available
        nfcAdapter = NfcAdapter.getDefaultAdapter(this);
        if (nfcAdapter == null) {
            // Stop here, we definitely need NFC
            Toast.makeText(this, "This device doesn't support NFC.", Toast.LENGTH_LONG).show();
            finish();
        }

        readFromIntent(getIntent());
        pendingIntent = PendingIntent.getActivity(this, 0, new Intent(this, getClass()).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP), 0);
        IntentFilter tagDetected = new IntentFilter(NfcAdapter.ACTION_TAG_DISCOVERED);
        tagDetected.addCategory(Intent.CATEGORY_DEFAULT);
        writeTagFilters = new IntentFilter[] { tagDetected };

        String path = Environment.getExternalStorageDirectory().toString() + "/buzz";
        File directory =new File(path);
        File[] files = directory.listFiles();
        for (File f : files){
            System.out.println(f.getName());
            if (f.getName().contains(".key"))
                node = new Node(f, context);
        }

        if (node == null)
            Toast.makeText(this, "No vendor key file found.", Toast.LENGTH_LONG).show();
        else {
            node.execute();
            System.out.print("XXX");
            System.out.print(node.getTransactions().toString());
            System.out.print("XXX");
            tvToolBar.setText(node.control.client.name);
        }

    }


    /**Read From NFC Tag*/
    private void readFromIntent(Intent intent) {

        String action = intent.getAction();
        if (NfcAdapter.ACTION_TAG_DISCOVERED.equals(action)
                || NfcAdapter.ACTION_TECH_DISCOVERED.equals(action)
                || NfcAdapter.ACTION_NDEF_DISCOVERED.equals(action)) {
            Parcelable[] rawMsgs = intent.getParcelableArrayExtra(NfcAdapter.EXTRA_NDEF_MESSAGES);
            NdefMessage[] msgs = null;
            if (rawMsgs != null) {
                msgs = new NdefMessage[rawMsgs.length];
                for (int i = 0; i < rawMsgs.length; i++) {
                    msgs[i] = (NdefMessage) rawMsgs[i];
                }
            }
            buildTagViews(msgs);

            btnSendTransaction.setVisibility(View.VISIBLE);

        }
    }

    private void buildTagViews(NdefMessage[] msgs) {

        if (msgs == null || msgs.length == 0) return;
        String text = "";
        byte[] payload = msgs[0].getRecords()[0].getPayload();
        int languageCodeLength = payload[0] & 0063; // Get the Language Code, e.g. "en"

        // Get the Text
        text = new String(payload, languageCodeLength + 1, payload.length - languageCodeLength - 1, StandardCharsets.ISO_8859_1);
        System.out.println(text);
        tvNFCContent.setText(text);

        //Display Balance
        String balance = "" + node.getBalance(tvNFCContent.getText().toString());
        tvBalance.setText(balance);
        tvBalance.setVisibility(View.VISIBLE);
        ivTag.setVisibility(View.INVISIBLE);
        tvStatus.setVisibility(View.INVISIBLE);

    }


    /*
        NFC STUFF
    */
    @Override
    protected void onNewIntent(Intent intent) {
        setIntent(intent);
        readFromIntent(intent);
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

    /**Enable Write*/
    private void WriteModeOn(){
        writeMode = true;
        nfcAdapter.enableForegroundDispatch(this, pendingIntent, writeTagFilters, null);
    }
    /**Disable Write*/
    private void WriteModeOff(){
        writeMode = false;
        nfcAdapter.disableForegroundDispatch(this);
    }
}