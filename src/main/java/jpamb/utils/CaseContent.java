package jpamb.utils;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.Scanner;
import java.util.concurrent.TimeoutException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public record CaseContent(
    Object[] params,
    ResultType result) {

  public String toString() {
    List<String> sparams = Arrays.asList(params).stream().map(a -> a.toString()).toList();

    return "(" + String.join(", ", sparams) + ") -> " + result.toString();
  }

  static Pattern paramPattern = Pattern.compile("\\(([^)]*)\\)");

  public static Object[] parseParams(String string) {
    Matcher matcher = paramPattern.matcher(string);
    if (matcher.find()) {
      ArrayList<Object> list = new ArrayList<>();
      try (Scanner sc = new Scanner(matcher.group(1))) {
        sc.useLocale(Locale.US);
        sc.useDelimiter(" *, *");
        while (sc.hasNext()) {
          if (sc.hasNextBoolean()) {
            list.add(sc.nextBoolean());
          } else if (sc.hasNextInt()) {
            list.add(sc.nextInt());
          } else {
            String var = sc.next();
            if (!var.equals(",")) {
              throw new RuntimeException("Invalid parameter: " + string + " // unexpected " + var);
            }
          }
        }
      }
      return list.toArray();
    } else {
      throw new RuntimeException(string + " is not a paramater list");
    }
  }

  public static CaseContent parse(String string) {
    Pattern pattern = Pattern.compile("(\\([^)]*\\))\\s*->\\s*(.+)");
    Matcher matcher = pattern.matcher(string);
    // Parse the expression
    if (matcher.find()) {
      String args = matcher.group(1);
      String result = matcher.group(2);
      return new CaseContent(parseParams(args), ResultType.parse(result));
    } else {
      throw new RuntimeException("Invalid case: " + string);
    }
  }

  public static enum ResultType {
    DIVIDE_BY_ZERO,
    ASSERTION_ERROR,
    SUCCESS,
    NON_TERMINATION,
    NULL_POINTER,
    OUT_OF_BOUNDS;

    public static ResultType parse(String string) {
      if (string.equals("*")) {
        return NON_TERMINATION;
      } else if (string.equals("assertion error")) {
        return ASSERTION_ERROR;
      } else if (string.equals("out of bounds")) {
        return OUT_OF_BOUNDS;
      } else if (string.equals("null pointer")) {
        return NULL_POINTER;
      } else if (string.equals("divide by zero")) {
        return DIVIDE_BY_ZERO;
      } else if (string.equals("ok")) {
        return SUCCESS;
      } else {
        throw new RuntimeException("Invalid result type: " + string);
      }
    }

    public String toString() {
      switch (this) {
        case DIVIDE_BY_ZERO:
          return "divide by zero";
        case ASSERTION_ERROR:
          return "assertion error";
        case OUT_OF_BOUNDS:
          return "out of bounds";
        case NULL_POINTER:
          return "null pointer";
        case NON_TERMINATION:
          return "*";
        case SUCCESS:
          return "ok";
        default:
          throw new RuntimeException("Unexpected");
      }
    }

    public static ResultType fromThrowable(Throwable cause) {
      if (cause instanceof ArithmeticException) {
        return DIVIDE_BY_ZERO;
      } else if (cause instanceof AssertionError) {
        return ASSERTION_ERROR;
      } else if (cause instanceof TimeoutException) {
        return NON_TERMINATION;
      } else if (cause instanceof ArrayIndexOutOfBoundsException) {
        return OUT_OF_BOUNDS;
      } else if (cause instanceof NullPointerException) {
        return NULL_POINTER;
      } else {
        throw new RuntimeException("Unexpected");
      }
    }
  }
}
